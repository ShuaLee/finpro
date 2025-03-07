from rest_framework import serializers
from .models import StockAccount, Stock


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['ticker', 'name', 'exchange', 'current_price', 'currency',
                  'dividends', 'sector', 'country', 'stock_type', 'last_updated']


class StockAccountSerializer(serializers.ModelSerializer):
    stocks = StockSerializer(many=True, read_only=True)

    class Meta:
        model = StockAccount
        fields = ['id', 'account_type', 'account_name', 'created_at', 'stocks']
