from django.utils import timezone
from rest_framework import serializers
from portfolio.models import StockPortfolio
from portfolio.utils import get_fx_rate
from schemas.models import StockPortfolioSCV
from stocks.models import Stock
from decimal import Decimal
from .constants import SCHEMA_COLUMN_CONFIG
from .models import SelfManagedAccount, ManagedAccount, StockHolding
import logging

logger = logging.getLogger(__name__)


class StockHoldingCreateSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(write_only=True)
    stock = serializers.PrimaryKeyRelatedField(read_only=True)
    confirm_add = serializers.BooleanField(
        write_only=True, required=False, default=False)

    class Meta:
        model = StockHolding
        fields = ['ticker', 'stock', 'quantity', 'purchase_price',
                  'purchase_date', 'investment_theme', 'confirm_add']

    def validate_ticker(self, value):
        return value.upper()

    def validate_purchase_date(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError(
                "Purchase date cannot be in the future.")
        return value

    def create(self, validated_data):
        account = self.context['self_managed_account']
        ticker = validated_data.pop('ticker').upper()
        confirm_add = validated_data.pop('confirm_add', False)

        stock = Stock.objects.filter(ticker=ticker).first()

        if not stock:
            if confirm_add:
                stock = Stock.create_from_ticker(ticker, is_custom=True)
                if not stock:
                    raise serializers.ValidationError(
                        {'ticker': f"Could not create stock for '{ticker}'."})
            else:
                raise serializers.ValidationError({
                    'ticker': f"Stock '{ticker}' not found in database.",
                    'non_field_errors': [
                        "To add this as a custom stock, please confirm by setting 'confirm_add': true."
                    ],
                    'resubmit_data': {
                        'ticker': ticker,
                        'quantity': validated_data.get('quantity'),
                        'purchase_price': validated_data.get('purchase_price'),
                        'purchase_date': validated_data.get('purchase_date'),
                        'investment_theme': validated_data.get('investment_theme'),
                    }
                })

        return StockHolding.objects.create(
            stock=stock,
            self_managed_account=account,
            **validated_data
        )


class StockHoldingSerializer(serializers.ModelSerializer):
    stock_ticker = serializers.CharField(source='stock.ticker', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)

    class Meta:
        model = StockHolding
        fields = ['id', 'stock_ticker', 'stock_name',
                  'quantity', 'purchase_price', 'purchase_date']


class SelfManagedAccountSerializer(serializers.ModelSerializer):
    holdings = StockHoldingSerializer(many=True, read_only=True)
    current_value_in_profile_fx = serializers.SerializerMethodField()

    def get_current_value_in_profile_fx(self, obj):
        total = 0
        holdings = obj.holdings.select_related(
            'stock').prefetch_related('column_values__column')
        for holding in holdings:
            val = holding.get_column_value('value_in_profile_fx')
            if val is not None:
                total += float(val)
        return round(total, 2)

    class Meta:
        model = SelfManagedAccount
        fields = ['id', 'name', 'current_value_in_profile_fx',
                  'created_at', 'holdings']


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(
        many=True, read_only=True)

    class Meta:
        model = StockPortfolio
        fields = ['created_at', 'self_managed_accounts']


class SelfManagedAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfManagedAccount
        fields = ['name', 'broker', 'tax_status', 'account_type']

    def create(self, validated_data):
        request = self.context['request']
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stockportfolio

        # Grab the default schema (assuming it's the first one)
        default_schema = stock_portfolio.schemas.first()

        if not default_schema:
            raise serializers.ValidationError(
                "No schema available for this stock portfolio."
            )

        # Attach the new account to the correct stock portfolio
        return SelfManagedAccount.objects.create(
            stock_portfolio=stock_portfolio,
            **validated_data
        )


class StockPortfolioSchemaColumnValueEditSerializer(serializers.ModelSerializer):
    value = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = StockPortfolioSCV
        fields = ['id', 'value']

    def validate(self, data):
        value = data.get('value')
        column = self.instance.column
        config = SCHEMA_COLUMN_CONFIG.get(
            column.source, {}).get(column.source_field)

        if not config:
            raise serializers.ValidationError("Invalid column configuration.")

        if not config.get('editable', False):
            raise serializers.ValidationError("This column is not editable.")

        data_type = config.get('data_type')

        if value is not None:
            if data_type == 'decimal':
                try:
                    float(value)
                except (ValueError, TypeError):
                    raise serializers.ValidationError(
                        {"value": "Must be a valid decimal number."})
            elif data_type == 'string':
                if not isinstance(value, str):
                    raise serializers.ValidationError(
                        {"value": "Must be a string."})
        return data

    def update(self, instance, validated_data):
        value = validated_data.get('value')
        column = instance.column

        # Get config
        config = SCHEMA_COLUMN_CONFIG.get(
            column.source, {}).get(column.source_field)
        if not config and column.source == 'custom':
            config = SCHEMA_COLUMN_CONFIG['custom'][None]

        if not config:
            raise serializers.ValidationError("Invalid column configuration.")

        if not config.get('editable'):
            raise serializers.ValidationError("This column is not editable.")

        data_type = config.get('data_type', 'string')

        # Coerce to correct type
        try:
            if data_type == 'decimal':
                # store as string but keep precision
                instance.value = str(round(float(value), 4))
            elif data_type == 'string':
                instance.value = str(value)
            else:
                instance.value = value
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                {"value": f"Invalid value for type {data_type}."})

        instance.is_edited = True
        instance.save()
        return instance


class ManagedAccountSerializer(serializers.ModelSerializer):
    current_value_in_profile_fx = serializers.SerializerMethodField()

    class Meta:
        model = ManagedAccount
        fields = [
            'id',
            'name',
            'broker',
            'tax_status',
            'account_type',
            'strategy',
            'currency',
            'invested_amount',
            'current_value',
            'current_value_in_profile_fx',
            'created_at'
        ]

    def get_current_value_in_profile_fx(self, obj):
        profile_currency = obj.stock_portfolio.portfolio.profile.currency
        fx = get_fx_rate(obj.currency, profile_currency)
        try:
            fx_decimal = Decimal(str(fx)) if fx else Decimal(1)
        except Exception:
            fx_decimal = Decimal(1)

        return round(obj.current_value * fx_decimal, 2)

    def create(self, validated_data):
        request = self.context['request']
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stockportfolio

        if 'currency' not in validated_data or not validated_data['currency']:
            validated_data['currency'] = profile.currency

        return ManagedAccount.objects.create(
            stock_portfolio=stock_portfolio,
            **validated_data
        )

    def update(self, instance, validated_data):
        for field in ['name', 'broker', 'tax_status', 'account_type', 'strategy', 'currency', 'invested_amount', 'current_value']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
