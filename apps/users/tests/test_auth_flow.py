from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models.portfolio import Portfolio
from subscriptions.models import AccountType, Plan
from users.models import EmailVerificationToken, User
from users.services.auth_service import AuthService


class AuthFlowTests(APITestCase):
    def setUp(self):
        self.usd, _ = FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar"})
        Country.objects.get_or_create(code="US", defaults={"name": "United States"})
        Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free",
                "description": "Basic plan",
                "max_stocks": 10,
                "allow_crypto": False,
                "allow_metals": False,
                "price_per_month": 0.00,
                "is_active": True,
            },
        )
        AccountType.objects.get_or_create(
            slug="individual",
            defaults={
                "name": "Individual Investor",
                "description": "Default account type",
            },
        )

    def test_register_bootstraps_profile_and_main_portfolio(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "newuser@example.com",
                "password": "StrongPass123!",
                "accept_terms": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="newuser@example.com")
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.currency.code, "USD")
        self.assertEqual(user.profile.plan.slug, "free")
        self.assertEqual(user.profile.account_type.slug, "individual")
        self.assertTrue(
            Portfolio.objects.filter(profile=user.profile, is_main=True).exists()
        )
        self.assertTrue(
            EmailVerificationToken.objects.filter(
                user=user,
                purpose=EmailVerificationToken.Purpose.VERIFY_EMAIL,
            ).exists()
        )

    def test_login_rejects_unverified_user(self):
        user = User.objects.create_user(
            email="pending@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("auth-login"),
            {"email": user.email, "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("verify your email", response.json()["detail"].lower())

    def test_failed_logins_trigger_lockout(self):
        user = User.objects.create_user(
            email="locked@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )

        for _ in range(AuthService.MAX_FAILED_LOGIN_ATTEMPTS):
            response = self.client.post(
                reverse("auth-login"),
                {"email": user.email, "password": "WrongPass123!"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user.refresh_from_db()
        self.assertIsNotNone(user.locked_until)
        self.assertEqual(user.failed_login_count, 0)

        response = self.client.post(
            reverse("auth-login"),
            {"email": user.email, "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("temporarily locked", response.json()["detail"].lower())
