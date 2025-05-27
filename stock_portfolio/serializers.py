from decimal import Decimal
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import StockPortfolio, SelfManagedAccount, SchemaColumnValue, SchemaColumn, StockHolding
import logging

logger = logging.getLogger(__name__)

class StockPortfolioSerializer(serializers.Serializer):
    class Meta:
        model = StockPortfolio
        fields = ['created_at']