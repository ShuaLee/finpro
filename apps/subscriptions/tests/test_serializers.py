"""
subscriptions.tests.test_serializers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for the PlanSerializer used in the subscriptions API.
"""

from django.test import TestCase
from subscriptions.models import Plan
from subscriptions.serializers import PlanSerializer


class PlanSerializerTests(TestCase):
    """
    Tests for PlanSerializer output.
    """

    def test_plan_serializer_fields(self):
        """
        Ensure serializer includes all expected fields.
        """
        plan = Plan.objects.create(
            name="Free",
            slug="free",
            description="Basic free plan",
            max_stocks=10,
            allow_crypto=False,
            allow_metals=False,
            price_per_month=0.00
        )

        serializer = PlanSerializer(plan)
        data = serializer.data

        expected_keys = {
            "name", "slug", "description", "max_stocks",
            "allow_crypto", "allow_metals", "price_per_month"
        }
        self.assertTrue(expected_keys.issubset(data.keys()))
