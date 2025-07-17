from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User
from users.services import bootstrap_user_profile


class ProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profileuser@example.com", password="securePass123"
        )
        bootstrap_user_profile(self.user)
        self.profile = self.user.profile
        self.profile_url = reverse("user-profile")

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_get_profile_requires_auth(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_success(self):
        self.authenticate()
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_update_profile_country_currency(self):
        self.authenticate()
        payload = {"country": "CA", "preferred_currency": "CAD"}
        response = self.client.patch(self.profile_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.country, "CA")
        self.assertEqual(self.profile.preferred_currency, "CAD")