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
from subscriptions.models import Plan, AccountType


class SignupTests(APITestCase):
    """
    Tests the user signup endpoint and its side effects.

    Scenarios:
    - Successful signup creates User, Profile, Portfolio, and assigns Free plan.
    - Optional profile fields are saved correctly.
    - JWT cookies (access, refresh) are set.
    - Missing required fields returns validation errors.
    """

    def setUp(self):
        self.url = reverse("signup")

        # Ensure Free plan and Individual account type exist for bootstrap logic
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
        self.individual_type = AccountType.objects.create(
            name="Individual Investor",
            slug="individual",
            description="Default account type for personal investors"
        )

    def test_signup_creates_user_profile_portfolio_with_defaults(self):
        """
        Ensure:
        - Signup returns 201 CREATED.
        - User is created with hashed password.
        - Profile exists with Free plan and Individual account type.
        - Country and currency defaults apply.
        - Portfolio exists for the user.
        - JWT cookies are set.
        """
        payload = {
            "email": "john@example.com",
            "password": "securePass123",
            "first_name": "John",
            "last_name": "Doe",
            "is_over_13": True,
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Validate response structure
        self.assertIn("detail", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], payload["email"])

        # Validate user exists with hashed password
        user = User.objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))

        # Validate profile defaults and optional fields
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.first_name, "John")
        self.assertEqual(profile.last_name, "Doe")
        self.assertEqual(profile.plan.slug, "free")
        self.assertEqual(profile.account_type.slug, "individual")
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.preferred_currency, "USD")
        self.assertEqual(profile.language, "en")  # Default from Accept-Language fallback

        # Validate portfolio exists
        portfolio = Portfolio.objects.get(profile=profile)
        self.assertIsNotNone(portfolio)

        # Validate JWT cookies exist
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)

    def test_signup_missing_required_field_returns_error(self):
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

    def test_signup_rejects_duplicate_email(self):
        """
        Ensure signup fails if the email is already registered.
        """
        User.objects.create_user(email="dup@example.com", password="testpass", is_over_13=True)
        payload = {
            "email": "dup@example.com",
            "password": "securePass123",
            "is_over_13": True,
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)