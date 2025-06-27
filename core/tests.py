from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import FXRate
from datetime import timedelta

User = get_user_model()

class CoreAppTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_signup_creates_user_profile_portfolio(self):
        response = self.client.post(
            '/api/auth/signup-complete/',
            {
                "email": "test@example.com",
                "password": "Helpome123",
                "first_name": "John",
                "last_name": "Doe",
                "birth_date": "2000-01-01"
            },
            content_type='application/json',
            HTTP_ACCEPT_LANGUAGE='en'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email="test@example.com").exists())
        user = User.objects.get(email="test@example.com")
        self.assertTrue(hasattr(user, 'profile'))
        self.assertTrue(hasattr(user.profile, 'portfolio'))

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
        print("Patch response:", response.status_code, response.content.decode())

        self.assertEqual(response.status_code, 200)
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.language, "fr")
        self.assertEqual(user.profile.currency, "EUR")

    def test_fxrate_staleness(self):
        recent = FXRate.objects.create(from_currency="USD", to_currency="EUR", rate=1.1)
        self.assertFalse(recent.is_stale())

        stale_time = timezone.now() - timedelta(days=2)
        FXRate.objects.filter(pk=recent.pk).update(updated_at=stale_time)
        recent.refresh_from_db()
        self.assertTrue(recent.is_stale())