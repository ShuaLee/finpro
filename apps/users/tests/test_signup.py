"""
users.tests.test_signup
~~~~~~~~~~~~~~~~~~~~~~~~
Tests for the signup API, verifying:
- User, Profile, and Portfolio are created successfully.
- Free plan is assigned by default.
- JWT authentication cookies are set (if implemented).
"""

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, Profile
from portfolios.models.portfolio import Portfolio
from subscriptions.models import Plan


class SignupTests(APITestCase):
    """
    Tests the user signup endpoint and related side effects.

    Scenarios:
    - Successful signup creates User, Profile, and Portfolio, and assigns Free plan.
    - Missing required fields (is_over_13) results in validation error.
    """

    def setUp(self):
        # Ensure this matches your signup URL name
        self.url = reverse("signup")

        # Create Free plan since it's required by bootstrap logic
        self.free_plan = Plan.objects.create(
            name="Free",
            slug="free",
            description="Default free plan",
            max_stocks=10,
            allow_crypto=False,
            allow_metals=False,
            price_per_month=0.00,
            is_active=True,
        )

    def test_signup_creates_user_profile_and_portfolio(self):
        """
        Ensure:
        - Signup request returns 201 CREATED.
        - User exists in DB.
        - Profile exists with Free plan assigned.
        - Portfolio exists for the user.
        - JWT cookies (access, refresh) are set if implemented.
        """
        payload = {
            "email": "john@example.com",
            "password": "securePass123",
            "first_name": "John",
            "is_over_13": True,
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Validate user exists
        user = User.objects.get(email=payload["email"])
        self.assertIsNotNone(user)

        # Validate profile exists with Free plan
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.plan.slug, "free")
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.preferred_currency, "USD")

        # Validate portfolio exists
        portfolio = Portfolio.objects.get(profile=profile)
        self.assertIsNotNone(portfolio)

        # Validate JWT cookies exist (if implemented)
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)

    def test_signup_missing_required_field_fails(self):
        """
        Ensure signup fails if 'is_over_13' is missing.
        """
        payload = {
            "email": "fail@example.com",
            "password": "securePass123",
            "first_name": "John",
            # Missing is_over_13
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_over_13", response.data)
