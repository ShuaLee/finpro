from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User

class JWTRefreshTests(APITestCase):
    def setUp(self):
        self.login_url = reverse("cookie-login")
        self.refresh_url = reverse("cookie-refresh")
        self.user = User.objects.create_user(
            email="jwtrefresh@example.com", password="securePass123"
        )

    def authenticate(self):
        """Login and return response to extract cookies."""
        payload = {"email": self.user.email, "password": "securePass123"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def test_refresh_issues_new_access_cookie(self):
        """After refresh, access cookie should change."""
        login_response = self.authenticate()
        old_access_cookie = login_response.cookies.get("access").value

        # Perform refresh using existing cookies
        self.client.cookies = login_response.cookies
        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_access_cookie = response.cookies.get("access").value
        self.assertNotEqual(old_access_cookie, new_access_cookie, "Access token was not refreshed")

    def test_refresh_fails_without_refresh_cookie(self):
        """Refresh should fail if no refresh token in cookies."""
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_rotated_refresh_token_cannot_be_reused(self):
        """Old refresh token should fail after it is used once."""
        login_response = self.authenticate()
        old_refresh_cookie = login_response.cookies["refresh"].value  # store old token

        # Use refresh once (rotation enabled, this sets a new refresh token in cookies)
        first_refresh = self.client.post(self.refresh_url)
        self.assertEqual(first_refresh.status_code, status.HTTP_200_OK)

        # ✅ Manually restore old refresh token for second attempt
        self.client.cookies["refresh"] = old_refresh_cookie
        second_refresh = self.client.post(self.refresh_url)

        # ✅ Old token should now fail
        self.assertEqual(second_refresh.status_code, status.HTTP_401_UNAUTHORIZED)