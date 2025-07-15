from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from portfolios.models import Portfolio
from users.models import Profile

User = get_user_model()


class SignupTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('auth-signup')  # Update this to match your router name

    def test_signup_creates_user_profile_portfolio(self):
        response = self.client.post(
            self.url,
            {
                "email": "test@example.com",
                "password": "Helpome123",
                "first_name": "John",
                "last_name": "Doe",
                "is_over_13": True
            },
            format='json',
            HTTP_ACCEPT_LANGUAGE='en'
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="test@example.com")
        self.assertTrue(hasattr(user, 'profile'))
        self.assertTrue(hasattr(user.profile, 'portfolio'))

    def test_signup_creates_profile_and_portfolio_with_defaults(self):
        response = self.client.post(
            self.url,
            {
                "email": "newuser@example.com",
                "password": "securepass123",
                "first_name": "Jane",
                "is_over_13": True
            },
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="newuser@example.com")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.preferred_currency, "USD")
        self.assertTrue(Portfolio.objects.filter(profile=profile).exists())

    def test_signup_with_custom_country_and_currency(self):
        response = self.client.post(
            self.url,
            {
                "email": "customuser@example.com",
                "password": "securepass123",
                "first_name": "John",
                "is_over_13": True,
                "country": "IN",
                "preferred_currency": "INR"
            },
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="customuser@example.com")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.country, "IN")
        self.assertEqual(profile.preferred_currency, "INR")

    def test_signup_requires_age_confirmation(self):
        response = self.client.post(
            self.url,
            {
                "email": "agecheck@example.com",
                "password": "securepass123",
                "first_name": "Alice",
                "is_over_13": False
            },
            format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("is_over_13", response.json())
