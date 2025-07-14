from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()

class SignupTests(TestCase):
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