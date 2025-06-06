from rest_framework import serializers
from stocks.models import Stock
from functools import reduce
from .constants import SCHEMA_COLUMN_CONFIG
from .models import StockPortfolio, SelfManagedAccount, StockPortfolioSchemaColumnValue, StockHolding
from .utils import set_nested_attr
import logging
import operator

logger = logging.getLogger(__name__)

class StockHoldingCreateSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(write_only=True)
    stock = serializers.PrimaryKeyRelatedField(read_only=True)
    confirm_add = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = StockHolding
        fields = ['ticker', 'stock','quantity', 'purchase_price', 'purchase_date', 'investment_theme', 'confirm_add']

    def validate_ticker(self, value):
        return value.upper()    

    def create(self, validated_data):
        account = self.context['self_managed_account']
        ticker = validated_data.pop('ticker').upper()
        confirm_add = validated_data.pop('confirm_add', False)

        stock = Stock.objects.filter(ticker=ticker).first()

        if not stock:
            if confirm_add:
                stock = Stock.create_from_ticker(ticker, is_custom=True)
                if not stock:
                    raise serializers.ValidationError({'ticker': f"Could not create stock for '{ticker}'."})
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
        fields = ['id', 'stock_ticker', 'stock_name', 'quantity', 'purchase_price', 'purchase_date']


class SelfManagedAccountSerializer(serializers.ModelSerializer):
    holdings = StockHoldingSerializer(many=True, read_only=True)

    class Meta:
        model = SelfManagedAccount
        fields = ['id', 'name', 'created_at', 'holdings']

class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(many=True, read_only=True)

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

        # Attach the new account to the correct stock portfolio
        return SelfManagedAccount.objects.create(
            stock_portfolio=stock_portfolio,
            **validated_data
        )

class StockPortfolioSchemaColumnValueEditSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dynamic_field_name = None  # For reference in to_representation

        column = self.instance.column if self.instance else None
        if column:
            source = column.source
            source_field = column.source_field
            config = SCHEMA_COLUMN_CONFIG.get(source, {}).get(source_field)
            if not config and source == 'custom':
                config = SCHEMA_COLUMN_CONFIG['custom'][None]
                source_field = 'value'

            input_key = source_field if source != 'custom' else 'value'
            self._dynamic_field_name = input_key
            data_type = config.get('data_type') if config else 'string'

            if data_type == 'decimal':
                self.fields[input_key] = serializers.DecimalField(max_digits=20, decimal_places=4)
            else:
                self.fields[input_key] = serializers.CharField()

    class Meta:
        model = StockPortfolioSchemaColumnValue
        fields = ['id']  # You'll override `to_representation` anyway

    def to_representation(self, instance):
        column = instance.column
        source = column.source
        source_field = column.source_field
        config = SCHEMA_COLUMN_CONFIG.get(source, {}).get(source_field)
        if not config and source == 'custom':
            config = SCHEMA_COLUMN_CONFIG['custom'][None]

        input_key = source_field if source != 'custom' else 'value'
        value = instance.get_value()

        return {
            "id": instance.id,
            input_key: value,
            "column": column.title,
            "editable": config.get('editable', False),
            "data_type": config.get('data_type', 'string'),
        }

    def validate(self, data):
        column_value = self.instance
        if not column_value.column.editable:
            raise serializers.ValidationError("This column is not editable.")
        return data
    
    def update(self, instance, validated_data):
        column = instance.column
        source = column.source
        source_field = column.source_field

        # Handle special case for custom
        config = SCHEMA_COLUMN_CONFIG.get(source, {}).get(source_field)

        if not config and source == 'custom':
            config = SCHEMA_COLUMN_CONFIG['custom'][None]

        if not config:
            raise serializers.ValidationError(f"Unsupported column source/field: {source}.{source_field}")

        if not config.get('editable', False):
            raise serializers.ValidationError(f"{source_field} is not editable.")

        # Determine field to extract from request
        input_key = source_field if source != 'custom' else 'value'
        if input_key not in validated_data:
            raise serializers.ValidationError({input_key: "This field is required."})

        raw_value = validated_data[input_key]

        # Attempt to cast the value based on data_type
        data_type = config.get('data_type')
        try:
            if data_type == 'decimal':
                casted_value = float(raw_value)
            elif data_type == 'string':
                casted_value = str(raw_value)
            else:
                casted_value = raw_value  # fallback, use as-is
        except (ValueError, TypeError):
            raise serializers.ValidationError({input_key: f"Invalid value for type {data_type}."})

        if source in ['holding', 'asset']:
            # Resolve field_path and set value
            field_path = config['field_path']
            if not field_path:
                raise serializers.ValidationError("Invalid field path.")
            
            parts = field_path.split('.')
            target = reduce(getattr, [instance] + parts[:-1])
            setattr(target, parts[-1], casted_value)
            target.save()

            instance.value = None
            instance.is_edited = False

        elif source == 'custom':
            instance.value = casted_value
            instance.is_edited = True

        elif source == 'calculated':
            raise serializers.ValidationError("Calculated columns cannot be edited.")

        else:
            raise serializers.ValidationError(f"Unknown source type '{source}'.")

        instance.save()
        return instance