from rest_framework import serializers
from .models import StockPortfolio, SelfManagedAccount


class SelfManagedAccountSerializer(serializers.ModelSerializer):
    active_schema_name = serializers.SerializerMethodField()

    class Meta:
        model = SelfManagedAccount
        fields = ['id', 'name', 'currency',
                  'broker', 'tax_status', 'account_type', 'use_default_schema', 'active_schema', 'active_schema_name']
        read_only_fields = ['id']

    def get_active_schema_name(self, obj):
        return obj.active_schema.name if obj.active_schema else None


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(
        many=True, read_only=True)

    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at', 'self_managed_accounts']
