"""
Stock Portfolio Serializers
---------------------------

Serializers for StockPortfolio model.
"""

from rest_framework import serializers
from portfolios.models.stock import StockPortfolio


class StockPortfolioSerializer(serializers.ModelSerializer):
    self_managed_schema = serializers.PrimaryKeyRelatedField(read_only=True)
    managed_schema = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = StockPortfolio
        fields = ["id", "portfolio", "self_managed_schema", "managed_schema"]
