from rest_framework import serializers
from portfolios.models import Portfolio, StockPortfolio


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