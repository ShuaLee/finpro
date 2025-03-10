from rest_framework import serializers
from django.db import IntegrityError
import yfinance as yf
from .models import StockAccount, Stock, StockHolding


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['ticker']


class StockHoldingSerializer(serializers.ModelSerializer):
    stock = StockSerializer()  # Nested serializer to include stock details

    class Meta:
        model = StockHolding
        fields = ['stock', 'shares']


class StockAccountSerializer(serializers.ModelSerializer):
    # Access stocks via StockHolding
    stocks = StockHoldingSerializer(
        source='stockholding_set', many=True, read_only=True)

    class Meta:
        model = StockAccount
        fields = ['id', 'account_name', 'account_type', 'stocks']


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
