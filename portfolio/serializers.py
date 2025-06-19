from rest_framework import serializers
from accounts.serializers import SelfManagedAccountSerializer
from .models import Portfolio, StockPortfolio


class PortfolioSerializer(serializers.ModelSerializer):
    stock_portfolio = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ['created_at', 'stock_portfolio']

    def get_stock_portfolio(self, obj):
        try:
            stock_portfolio = StockPortfolio.objects.get(portfolio=obj)
            return {
                'created_at': stock_portfolio.created_at,
            }
        except StockPortfolio.DoesNotExist:
            return None


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_accounts = SelfManagedAccountSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = StockPortfolio
        fields = ['id', 'created_at', 'self_managed_account']
