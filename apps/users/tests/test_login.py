from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User


class LoginTests(APITestCase):
    def setUp(self):
        self.url = reverse("cookie-login")
        self.user = User.objects.create_user(
            email="loginuser@example.com", password="securePass123"
        )

    def test_login_success_sets_jwt_cookies(self):
        payload = {"email": "loginuser@example.com", "password": "securePass123"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ✅ Check cookies exist
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)
        # ✅ Optional security attributes check
        for cookie in ["access", "refresh"]:
            self.assertTrue(response.cookies[cookie]["httponly"])
            self.assertEqual(response.cookies[cookie]["samesite"].lower(), "lax")

    def test_login_fails_invalid_credentials(self):
        payload = {"email": "loginuser@example.com", "password": "wrongPass"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_fails_missing_email(self):
        payload = {"password": "securePass123"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_login_fails_missing_password(self):
        payload = {"email": "loginuser@example.com"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)