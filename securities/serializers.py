from rest_framework import serializers
from .models import StockAccount


class StockAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAccount
        fields = ['id', 'account_type', 'account_name', 'created_at']
