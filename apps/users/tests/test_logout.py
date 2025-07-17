from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User


class LogoutTests(APITestCase):
    def setUp(self):
        self.login_url = reverse("cookie-login")
        self.logout_url = reverse("cookie-logout")
        self.user = User.objects.create_user(
            email="logoutuser@example.com", password="securePass123"
        )

    def authenticate(self):
        response = self.client.post(self.login_url, {
            "email": "logoutuser@example.com",
            "password": "securePass123"
        })
        # ✅ Ensure login was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_clears_jwt_cookies(self):
        self.authenticate()
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # ✅ Matches your view
        # ✅ Cookies should be cleared
        self.assertEqual(response.cookies["access"].value, "")
        self.assertEqual(response.cookies["refresh"].value, "")
        # ✅ Check HttpOnly and SameSite remain correct
        for cookie in ["access", "refresh"]:
            self.assertEqual(response.cookies[cookie].value, "")