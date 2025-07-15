"""
Metal Portfolio Serializers
---------------------------

Serializers for MetalPortfolio model.
"""

from rest_framework import serializers
from portfolios.models.metal import MetalPortfolio


class MetalPortfolioSerializer(serializers.ModelSerializer):
    """
    Serializer for MetalPortfolio.
    """
    class Meta:
        model = MetalPortfolio
        fields = ["id", "portfolio", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        raise NotImplementedError(
            "Use metal_service.create_metal_portfolio() to create MetalPortfolio."
        )
