from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User

class AuthStatusTests(APITestCase):
    def setUp(self):
        self.url = reverse("auth-status")
        self.login_url = reverse("cookie-login")
        self.user = User.objects.create_user(
            email="statususer@example.com", password="securePass123"
        )

    def test_status_requires_auth(self):
        """Should return 401 for anonymous user."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_status_authenticated_user(self):
        """Should return isAuthenticated=True for logged-in user."""
        # Login to get cookies
        login_response = self.client.post(self.login_url, {
            "email": self.user.email,
            "password": "securePass123"
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Carry over cookies
        self.client.cookies = login_response.cookies

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("isAuthenticated", response.data)
        self.assertTrue(response.data["isAuthenticated"])
