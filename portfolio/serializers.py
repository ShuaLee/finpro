from rest_framework import serializers
from .models import Portfolio
from securities.models import StockAccount
from securities.serializers import StockAccountSerializer, StockPortfolioSerializer


class PortfolioSerializer(serializers.ModelSerializer):
    stock_portfolio = StockPortfolioSerializer(read_only=True)

    class Meta:
        model = Portfolio
        fields = ['id', 'created_at', 'stock_portfolio']
