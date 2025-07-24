"""
Portfolio Serializer
--------------------

Serializes the main Portfolio object, including nested asset-specific sub-portfolios
(e.g., stocks, metals) for display purposes.

Notes:
- `profile` is read-only because it's determined by the authenticated user.
- Sub-portfolios are nested as read-only fields since they are created via separate endpoints.
"""

from rest_framework import serializers
from portfolios.models.metal import Portfolio
from portfolios.serializers.stock import StockPortfolioSerializer
from portfolios.serializers.metal import MetalPortfolioSerializer


class PortfolioSerializer(serializers.ModelSerializer):
    """
    Serializer for the main Portfolio model.

    Fields:
    - id: Primary key
    - profile: Read-only reference to the user's profile
    - created_at: Timestamp when the portfolio was created
    - stock_portfolio: Nested representation if exists
    - metal_portfolio: Nested representation if exists
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
        read_only_fields = ["id", "created_at", "profile"]

    def create(self, validated_data):
        """
        Prevent direct creation via serializer.
        Use the service layer (portfolio_service.create_portfolio).
        """
        raise NotImplementedError(
            "Use portfolio_service.create_portfolio() to create a Portfolio."
        )
