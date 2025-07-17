"""
users.tests.test_signup
~~~~~~~~~~~~~~~~~~~~~~~~
Tests for the signup API endpoint, focusing on:
- Successful user registration.
- Automatic profile creation with default plan and account type.
- Application of optional profile fields.
- JWT cookies for session management.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from subscriptions.models import AccountType, Plan
from users.models import User, Profile


class SignupTests(APITestCase):
    """
    Test suite for user signup workflow.

    Covers:
    - Successful signup flow.
    - Defaults for profile fields.
    - Optional fields behavior.
    - Validation errors for missing/invalid input.
    """

    def setUp(self):
        self.url = reverse("signup")
        self.free_plan = Plan.objects.get(slug="free")
        self.individual_type = AccountType.objects.get(slug="individual")

    def test_signup_success_creates_user_and_profile(self):
        """
        Test successful signup:
        - Creates user and profile with defaults.
        - Sets JWT cookies for session-based auth.
        - Ensures cookie security attributes and expiry.
        """
        payload = {
            "email": "john@example.com",
            "password": "securePass123",
            "is_over_13": True
        }

        # Perform request
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # ✅ Validate response structure
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Signup successful")

        self.assertIn("user", response.data)
        user_data = response.data["user"]
        self.assertIn("id", user_data)
        self.assertEqual(user_data["email"], payload["email"])
        self.assertNotIn("password", user_data)

        # ✅ Check user and profile creation
        user = User.objects.filter(email=payload["email"]).first()
        self.assertIsNotNone(user)
        profile = Profile.objects.filter(user=user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.plan.slug, "free")
        self.assertEqual(profile.account_type.slug, "individual")

        # ✅ Validate JWT cookies exist
        access_cookie = response.cookies.get("access")
        refresh_cookie = response.cookies.get("refresh")
        self.assertIsNotNone(access_cookie, "Access token cookie missing")
        self.assertIsNotNone(refresh_cookie, "Refresh token cookie missing")

        # ✅ Validate security attributes
        for cookie in [access_cookie, refresh_cookie]:
            self.assertTrue(cookie["httponly"], "Cookie is not HttpOnly")
            self.assertEqual(cookie["samesite"].lower(), "lax")
            # Optional: Add HTTPS check if running in production
            # self.assertTrue(cookie.get("secure", False), "Cookie should be Secure in production")

        # ✅ Validate expiry exists
        self.assertIn("expires", access_cookie.output())
        self.assertIn("expires", refresh_cookie.output())

    def test_signup_missing_age_confirmation_fails(self):
        """
        Test signup fails if 'is_over_13' is missing.
        """
        payload = {
            "email": "fail@example.com",
            "password": "securePass123"
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_over_13", response.data)

    def test_signup_rejects_if_under_13(self):
        """
        Test signup fails when 'is_over_13' is explicitly False.
        """
        payload = {
            "email": "underage@example.com",
            "password": "securePass123",
            "is_over_13": False
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_over_13", response.data)

    def test_signup_rejects_duplicate_email(self):
        """
        Test signup fails for duplicate email.
        """
        User.objects.create_user(
            email="john@example.com", password="securePass123")

        payload = {
            "email": "john@example.com",
            "password": "securePass123",
            "is_over_13": True
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_signup_rejects_weak_password(self):
        """Test signup fails when password does not meet policy."""
        payload = {
            "email": "weakpass@example.com",
            "password": "123",  # Too short and numeric
            "is_over_13": True
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertTrue(
            any("too short" in msg.lower() or "too common" in msg.lower()
                for msg in response.data["password"])
        )
