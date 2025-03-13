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
        fields = ['ticker', 'currency']


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
        custom_cols = self.context.get('custom_columns', {})
        price_data = custom_cols.get('price')
        if price_data and price_data.get('override') and price_data.get('value') is not None:
            return Decimal(str(price_data['value']))
        data = obj.stock.fetch_yfinance_data(['price'])
        price = data.get('price')
        return Decimal(str(price)) if price is not None else None

    def get_total_investment(self, obj):
        price = self.get_price(obj)
        if price is not None:
            return price * obj.shares  # Both are Decimal now
        return None

    def get_dividends(self, obj):
        custom_cols = self.context.get('custom_columns', {})
        div_data = custom_cols.get('dividends')
        if div_data and div_data.get('override') and div_data.get('value') is not None:
            return Decimal(str(div_data['value']))
        data = obj.stock.fetch_yfinance_data(['dividends'])
        dividends = data.get('dividends')
        return Decimal(str(dividends)) if dividends is not None else None

    def to_representation(self, instance):
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
    # stock_accounts = StockAccountSerializer(many=True, read_only=True)

    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at']
