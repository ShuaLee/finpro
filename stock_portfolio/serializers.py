from decimal import Decimal
from django.core.exceptions import ValidationError
from rest_framework import serializers
from stocks.models import Stock
from .models import StockPortfolio, SelfManagedAccount, SchemaColumnValue, SchemaColumn, StockHolding
import logging

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
        fields = ['id', 'name', 'currency', 'created_at', 'holdings']

class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(many=True, read_only=True)

    class Meta:
        model = StockPortfolio
        fields = ['created_at', 'self_managed_accounts']

class SelfManagedAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfManagedAccount
        fields = ['name', 'currency', 'broker', 'tax_status', 'account_type']

    def create(self, validated_data):
        request = self.context['request']
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stockportfolio

        # Attach the new account to the correct stock portfolio
        return SelfManagedAccount.objects.create(
            stock_portfolio=stock_portfolio,
            **validated_data
        )