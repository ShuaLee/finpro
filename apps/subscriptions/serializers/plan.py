"""
subscriptions.serializers
~~~~~~~~~~~~~~~~~~~~~~~~~~
Serializers for handling subscription plan data representation in API responses.
"""

from rest_framework import serializers
from subscriptions.models import Plan


class PlanSerializer(serializers.ModelSerializer):
    """
    Serializer for the Plan model.

    Converts Plan instances into JSON representations for API responses.
    Only includes relevant public fields (e.g., name, slug, features, price).

    Attributes:
        name (str): Human-readable plan name (e.g., "Free", "Premium").
        slug (str): URL-safe identifier for the plan.
        description (str): Description of the plan's features.
        max_stocks (int): Maximum stocks allowed in this plan.
        allow_crypto (bool): Whether crypto assets are supported.
        allow_metals (bool): Whether metals are supported.
        price_per_month (decimal): Monthly subscription cost.
    """
    class Meta:
        model = Plan
        fields = [
            "name",
            "slug",
            "description",
            "max_stocks",
            "allow_crypto",
            "allow_metals",
            "price_per_month",
        ]
