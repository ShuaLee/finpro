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

    def test_signup_creates_profile_and_portfolio_with_defaults(self):
        url = reverse('auth-signup')
        data = {"email": "newuser@example.com", "password": "securepass123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="newuser@example.com")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.preferred_currency, "USD")
        self.assertTrue(Portfolio.objects.filter(profile=profile).exists())

    def test_signup_with_custom_values(self):
        url = reverse('auth-signup')
        data = {
            "email": "customuser@example.com",
            "password": "securepass123",
            "account_type": "manager",
            "plan": "premium",
            "country": "IN",
            "preferred_currency": "INR"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="customuser@example.com")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.account_type, "manager")
        self.assertEqual(profile.plan, "premium")
        self.assertEqual(profile.country, "IN")
        self.assertEqual(profile.preferred_currency, "INR")

    def test_signup_with_custom_country_and_currency(self):
        url = reverse('auth-signup')
        data = {
            "email": "customuser@example.com",
            "password": "securepass123",
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": "2000-01-01",
            "country": "IN",
            "preferred_currency": "INR"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="customuser@example.com")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.country, "IN")
        self.assertEqual(profile.preferred_currency, "INR")