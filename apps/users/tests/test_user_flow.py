"""
users.tests.test_user_flow
~~~~~~~~~~~~~~~~~~~~~~~~~~~
End-to-end tests for user signup, profile initialization,
and portfolio creation with default subscription plan.
"""

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, Profile
from portfolios.models.portfolio import Portfolio
from subscriptions.models import Plan, AccountType


class UserSignupFlowTests(APITestCase):
    """
    Verify the full signup flow:
    - Creates User
    - Bootstraps Profile with default Free plan & Individual account type
    - Creates Portfolio linked to Profile
    """

    def setUp(self):
        """
        Prepare necessary data:
        - Create Free plan
        - Create AccountType (Individual)
        - Set signup URL
        """
        self.free_plan, _ = Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free",
                "description": "Basic plan",
                "max_stocks": 10,
                "allow_crypto": False,
                "allow_metals": False,
                "price_per_month": 0.00,
                "is_active": True
            }
        )
        self.account_type, _ = AccountType.objects.get_or_create(
            slug="individual",
            defaults={
                "name": "Individual Investor",
                "description": "Default account type"
            }
        )
        self.signup_url = reverse("signup")

    def test_user_signup_creates_profile_and_portfolio(self):
        """
        Ensure:
        - Signup creates User.
        - Profile exists with Free plan, Individual account type, and defaults (US, USD).
        - Portfolio is created for the user.
        """
        payload = {
            "email": "newuser@example.com",
            "password": "securePass123",
            "is_over_13": True
        }

        response = self.client.post(self.signup_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify User exists
        user = User.objects.get(email="newuser@example.com")
        self.assertIsNotNone(user)

        # Verify Profile created with defaults
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.plan.slug, "free")
        self.assertEqual(profile.account_type.slug, "individual")
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.preferred_currency, "USD")
        self.assertEqual(profile.language, "en")

        # Verify Portfolio created
        portfolio = Portfolio.objects.get(profile=profile)
        self.assertIsNotNone(portfolio)

    def test_signup_requires_age_confirmation(self):
        """
        Ensure signup fails if is_over_13 is False.
        """
        payload = {
            "email": "failuser@example.com",
            "password": "securePass123",
            "is_over_13": False
        }
        response = self.client.post(self.signup_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_over_13", response.data)