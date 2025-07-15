"""
Portfolio Serializers
----------------------

This module defines serializers for the main Portfolio model.
"""

from rest_framework import serializers
from portfolios.models.metal import Portfolio
from apps.portfolios.serializers.stock import StockPortfolioSerializer
from apps.portfolios.serializers.metal import MetalPortfolioSerializer


class PortfolioSerializer(serializers.ModelSerializer):
    """
    Serializer for the Portfolio model.

    Related sub-portfolios (stock, metal, etc.) are included as read-only.
    They are created separately through dedicated endpoints.
    """
    stock_portfolio = StockPortfolioSerializer(read_only=True)
    metal_portfolio = MetalPortfolioSerializer(read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "profile",
            "created_at",
            "stock_portfolio",
            "metal_portfolio",
        ]
        read_only_fields = ["id", "created_at", "profile_setup_complete"]

    def create(self, validated_data):
        raise NotImplementedError(
            "Portfolio creation should be handled by portfolio_service.create_portfolio()."
        )
