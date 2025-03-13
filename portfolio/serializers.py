from rest_framework import serializers
from .models import IndividualPortfolio
from securities.models import StockAccount
from securities.serializers import StockAccountSerializer, StockPortfolioSerializer


class IndividualPortfolioSerializer(serializers.ModelSerializer):
    stock_portfolio = StockPortfolioSerializer(read_only=True)

    class Meta:
        model = IndividualPortfolio
        fields = ['id', 'created_at', 'stock_portfolio']
