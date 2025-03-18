from rest_framework import serializers
from .models import Portfolio
from securities.serializers import StockPortfolioSerializer


class PortfolioSerializer(serializers.ModelSerializer):
    stock_portfolio = StockPortfolioSerializer(read_only=True)

    class Meta:
        model = Portfolio
        fields = ['id', 'created_at', 'stock_portfolio']
