from rest_framework import serializers
from .models import StockPortfolio, SelfManagedAccount


class SelfManagedAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfManagedAccount
        fields = ['id', 'name', 'currency',
                  'broker', 'tax_status', 'account_type']
        read_only_fields = ['id']


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(
        many=True, read_only=True)

    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at', 'self_managed_accounts']
