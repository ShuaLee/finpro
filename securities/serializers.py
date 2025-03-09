from rest_framework import serializers
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

    class Meta:
        model = StockHolding
        fields = ['ticker', 'shares']

    def create(self, validated_data):
        # Get or create the Stock instance based on ticker
        ticker = validated_data.pop('ticker')
        stock, _ = Stock.objects.get_or_create(ticker=ticker)
        # Create StockHolding with the stock_account from context
        stock_account = self.context['stock_account']
        return StockHolding.objects.create(stock_account=stock_account, stock=stock, **validated_data)
