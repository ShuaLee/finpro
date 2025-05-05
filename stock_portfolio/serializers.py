from rest_framework import serializers
from .models import StockPortfolio, SelfManagedAccount

class StockPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at']

class SelfManagedAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfManagedAccount
        fields = ['id', 'name', 'currency', 'broker', 'tax_status', 'account_type']
        read_only_fields = ['id']