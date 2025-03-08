from rest_framework import serializers
from .models import IndividualPortfolio
from securities.models import StockAccount
from securities.serializers import StockAccountSerializer


class IndividualPortfolioSerializer(serializers.ModelSerializer):
    stock_accounts = StockAccountSerializer(
        many=True, read_only=True)

    class Meta:
        model = IndividualPortfolio
        fields = ['id', 'profile', 'name', 'created_at', 'stock_accounts']
