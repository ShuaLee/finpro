from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import SupportedCountry, SupportedCurrency


class ProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="profile@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.user)
        SupportedCountry.objects.create(code="CA", name="Canada")
        SupportedCurrency.objects.create(code="CAD", name="Canadian Dollar")

    def test_me_returns_user_and_profile(self):
        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["email"], self.user.email)
        self.assertEqual(response.data["profile"]["currency"], self.user.profile.currency)

    def test_profile_patch_updates_profile_fields(self):
        response = self.client.patch(
            "/api/v1/profile/",
            {
                "full_name": "Updated Name",
                "timezone": "America/Toronto",
                "country": "CA",
                "currency": "CAD",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.full_name, "Updated Name")
        self.assertEqual(self.user.profile.timezone, "America/Toronto")
        self.assertEqual(self.user.profile.country, "CA")
        self.assertEqual(self.user.profile.currency, "CAD")
