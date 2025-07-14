from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()

class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_profile_update(self):
        user = User.objects.create_user(
            email="jane@example.com", password="Helpome123",
            first_name="Jane", last_name="Doe", birth_date="2000-01-01"
        )

        login_response = self.client.post(
            '/auth/jwt/create/',
            {
                "email": "jane@example.com",
                "password": "Helpome123"
            },
            content_type='application/json'
        )

        self.assertEqual(login_response.status_code, 200)

        access_token = login_response.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + access_token)

        response = self.client.patch('/api/profile/', {
            "language": "fr",
            "currency": "EUR"
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        user.profile.refresh_from_db()
        self.assertEqual(user.profile.language, "fr")
        self.assertEqual(user.profile.currency, "EUR")