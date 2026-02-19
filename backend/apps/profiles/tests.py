from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from fx.models.country import Country
from fx.models.fx import FXCurrency
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class ProfileAPITests(APITestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar"})
        FXCurrency.objects.get_or_create(code="CAD", defaults={"name": "Canadian Dollar"})
        Country.objects.get_or_create(code="US", defaults={"name": "United States"})
        Country.objects.get_or_create(code="CA", defaults={"name": "Canada"})
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
        self.user = User.objects.create_user(
            email="profileuser@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        ProfileBootstrapService.bootstrap(user=self.user)
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get(reverse("profile-detail"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["email"], self.user.email)
        self.assertEqual(response.json()["currency"], "USD")

    def test_patch_profile(self):
        response = self.client.patch(
            reverse("profile-detail"),
            {"full_name": "Josh Fin", "currency": "CAD"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["full_name"], "Josh Fin")
        self.assertEqual(response.json()["currency"], "CAD")

    def test_complete_onboarding(self):
        response = self.client.post(
            reverse("profile-complete"),
            {"full_name": "Josh Fin", "country": "CA", "currency": "CAD"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["onboarding_status"], "completed")
        self.assertEqual(response.json()["onboarding_step"], 100)
        self.assertEqual(response.json()["country"], "CA")
        self.assertEqual(response.json()["currency"], "CAD")
