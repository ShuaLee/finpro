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
