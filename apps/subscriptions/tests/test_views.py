"""
subscriptions.tests.test_views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for subscription-related API endpoints.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from subscriptions.models import Plan


class PlanListAPITests(APITestCase):
    """
    Tests for the GET /subscriptions/plans/ endpoint.
    """

    def setUp(self):
        """
        Create sample plans for testing.
        """
        self.free_plan = Plan.objects.create(
            name="Free",
            slug="free",
            description="Basic plan",
            max_stocks=10,
            allow_crypto=False,
            allow_metals=False,
            price_per_month=0.00,
            is_active=True
        )

        self.premium_plan = Plan.objects.create(
            name="Premium",
            slug="premium",
            description="Premium plan",
            max_stocks=9999,
            allow_crypto=True,
            allow_metals=True,
            price_per_month=9.99,
            is_active=True
        )

        # Inactive plan should not be returned
        self.inactive_plan = Plan.objects.create(
            name="Legacy",
            slug="legacy",
            description="Old plan",
            max_stocks=50,
            allow_crypto=False,
            allow_metals=False,
            price_per_month=4.99,
            is_active=False
        )

        self.url = reverse('plan-list')

    def test_list_plans_returns_active_plans_only(self):
        """
        Ensure the API returns only active plans and excludes inactive ones.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 2)

        slugs = [plan['slug'] for plan in data]
        self.assertIn('free', slugs)
        self.assertIn('premium', slugs)
        self.assertNotIn('legacy', slugs)

    def test_plan_fields_structure(self):
        """
        Ensure each plan includes the expected fields in the response.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        plan_data = response.json()[0]
        expected_keys = {
            "name", "slug", "description", "max_stocks",
            "allow_crypto", "allow_metals", "price_per_month"
        }
        self.assertTrue(expected_keys.issubset(plan_data.keys()))
