from rest_framework import serializers
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import yfinance as yf
from .models import StockAccount, Stock, StockHolding, StockTag, StockPortfolio


class StockTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTag
        fields = ['id', 'name', 'arent']


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['ticker']


class StockHoldingSerializer(serializers.ModelSerializer):
    stock = StockSerializer()  # Nested serializer to include stock details
    price = serializers.SerializerMethodField()
    total_investment = serializers.SerializerMethodField()
    dividends = serializers.SerializerMethodField()
    stock_tags = StockTagSerializer(many=True)

    class Meta:
        model = StockHolding
        fields = [
            'stock', 'shares', 'purchase_price', 'stock_tags',
            'price', 'total_investment', 'dividends'
        ]

    def get_price(self, obj):
        if not obj.stock.last_updated or (timezone.now() - obj.stock.last_updated) > timedelta(hours=1):
            obj.stock.update_from_yfinance()
        return obj.stock.price

    def get_total_investment(self, obj):
        price = self.get_price(obj)
        if price is not None:
            return Decimal(str(price)) * obj.shares  # Convert float to Decimal
        return None

    def get_dividends(self, obj):
        if not obj.stock.last_updated or (timezone.now() - obj.stock.last_updated) > timedelta(hours=1):
            obj.stock.update_from_yfinance()
        return obj.stock.dividends

    def to_representation(self, instance):
        # Should be correct
        self.context['custom_columns'] = instance.stock_account.stock_portfolio.custom_columns
        representation = super().to_representation(instance)
        allowed_columns = instance.stock_account.stock_portfolio.custom_columns.keys(
        ) or instance.stock_account.stock_portfolio.get_default_columns().keys()
        filtered = {'stock': representation['stock']}
        filtered.update(
            {key: value for key, value in representation.items(
            ) if key in allowed_columns and key != 'stock'}
        )
        return filtered


class StockAccountSerializer(serializers.ModelSerializer):
    stocks = StockHoldingSerializer(
        source='stockholding_set', many=True, read_only=True)

    class Meta:
        model = StockAccount
        fields = ['id', 'account_name', 'account_type', 'created_at', 'stocks']


class StockHoldingCreateSerializer(serializers.ModelSerializer):
    """
    StockHoldingCreateSerilaizer: Uses ticker (a string) instead of requiring a Stock object ID,
    making it user-friendly. It creates or fetches the Stock and links it to the StockAccount.
    """
    ticker = serializers.CharField(write_only=True)

    def validate_ticker(self, value):
        """
        Verify the ticker exists using yfinance.
        """
        ticker = value.upper()
        try:
            stock = yf.Ticker(ticker)
            info = stock.info  # Fetch basic info to verify
            if not info or 'symbol' not in info or info['symbol'] != ticker:
                raise serializers.ValidationError(
                    f"Ticker '{ticker}' is not valid.")
        except Exception as e:
            raise serializers.ValidationError(
                f"Unable to verify ticker '{ticker}': {str(e)}")
        return ticker

    def create(self, validated_data):
        ticker = validated_data.pop('ticker')
        stock, _ = Stock.objects.get_or_create(ticker=ticker)
        stock_account = self.context['stock_account']
        try:
            return StockHolding.objects.create(stock_account=stock_account, stock=stock, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                f"Stock '{ticker}' is already in this account.")

    class Meta:
        model = StockHolding
        fields = ['ticker', 'shares']


class StockPortfolioSerializer(serializers.ModelSerializer):
    stock_accounts = StockAccountSerializer(many=True, read_only=True)

    class Meta:
        model = StockPortfolio
        fields = ['id', 'name', 'created_at',
                  'stock_accounts', 'custom_columns']

    def validate_custom_columns(self, value):
        for col, data in value.items():
            if data is not None:
                if not isinstance(data, dict) or 'override' not in data or 'value' not in data:
                    raise serializers.ValidationError(
                        f"Invalid format for column '{col}'. Use {{'value': <val>, 'override': bool}} or null.")
                if not isinstance(data['override'], bool):
                    raise serializers.ValidationError(
                        f"'override' for '{col}' must be a boolean.")
        return value
