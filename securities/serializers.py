from rest_framework import serializers
from django.db import IntegrityError
from decimal import Decimal
import yfinance as yf
from .models import StockAccount, Stock, StockHolding, StockTag


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
        ticker = yf.Ticker(obj.stock.ticker)
        return ticker.info.get('currentPrice', None)

    def get_total_investment(self, obj):
        price = self.get_price(obj)
        if price is not None:
            return Decimal(str(price)) * obj.shares  # Convert float to Decimal
        return None

    def get_dividends(self, obj):
        ticker = yf.Ticker(obj.stock.ticker)
        return ticker.info.get('dividendRate', None)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        stock_account = instance.stock_account
        allowed_columns = stock_account.custom_columns or stock_account.get_default_columns()
        # Ensure 'stock' is always included, then filter others
        filtered = {'stock': representation['stock']}
        filtered.update(
            {key: value for key, value in representation.items(
            ) if key in allowed_columns and key != 'stock'}
        )
        return filtered


class StockAccountSerializer(serializers.ModelSerializer):
    # Access stocks via StockHolding
    stocks = StockHoldingSerializer(
        source='stockholding_set', many=True, read_only=True)
    custom_columns = serializers.ListField(
        child=serializers.CharField(), required=False)

    class Meta:
        model = StockAccount
        fields = ['id', 'account_name', 'account_type',
                  'created_at', 'stocks', 'custom_columns']


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
