from rest_framework import serializers
from accounts.serializers.stocks import SelfManagedAccountSerializer
from models import StockPortfolio


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at', 'self_managed_account']
