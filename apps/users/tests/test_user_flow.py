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
from portfolios.models import Portfolio
from subscriptions.models import Plan


class UserSignupFlowTests(APITestCase):
    """
    Verify the full signup flow:
    - User registration
    - Profile created with default Free plan
    - Portfolio created for user
    """

    def setUp(self):
        # Ensure Free plan exists (should be created by AppConfig)
        self.free_plan, _ = Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free",
                "description": "Basic plan",
                "max_stocks": 10,
                "allow_crypto": False,
                "allow_metals": False,
                "price_per_month": 0.00,
            }
        )
        # Update with your signup route name
        self.signup_url = reverse("signup")

    def test_user_signup_creates_profile_and_portfolio(self):
        """
        Ensure signing up a new user:
        - Creates a User record
        - Creates a Profile with default Free plan
        - Creates a Portfolio linked to that profile
        """
        payload = {
            "email": "newuser@example.com",
            "password": "securePass123",
            "first_name": "John",
            "is_over_13": True
        }

        response = self.client.post(self.signup_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify user exists
        user = User.objects.get(email="newuser@example.com")
        self.assertIsNotNone(user)

        # Verify profile created with Free plan
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.plan.slug, "free")
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.preferred_currency, "USD")

        # Verify portfolio created
        portfolio = Portfolio.objects.get(profile=profile)
        self.assertIsNotNone(portfolio)

    def test_signup_requires_age_confirmation(self):
        """
        Ensure signup fails if is_over_13 is False.
        """
        payload = {
            "email": "failuser@example.com",
            "password": "securePass123",
            "first_name": "John",
            "is_over_13": False
        }
        response = self.client.post(self.signup_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_over_13", response.data)
