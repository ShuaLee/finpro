"""
Stock Portfolio Serializers
---------------------------

Serializers for StockPortfolio model.
"""

from rest_framework import serializers
from portfolios.models import StockPortfolio


class StockPortfolioSerializer(serializers.ModelSerializer):
    """
    Serializer for StockPortfolio.

    Only provides basic representation; creation should be done via service layer.
    """
    class Meta:
        model = StockPortfolio
        fields = ["id", "portfolio", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        """
        Prevent direct creation through serializer.
        """
        raise NotImplementedError(
            "Use stock_service.create_stock_portfolio() to create StockPortfolio."
        )
