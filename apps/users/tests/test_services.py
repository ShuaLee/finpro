"""
Tests for Users Services
-------------------------
Validates domain logic in users.services module.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import Profile
from portfolios.models import Portfolio
from users.services import bootstrap_user_profile_and_portfolio

User = get_user_model()


class UserServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            first_name="John",
            is_over_13=True
        )

    def test_bootstrap_creates_profile_and_portfolio(self):
        profile = bootstrap_user_profile_and_portfolio(self.user)
        self.assertIsInstance(profile, Profile)
        self.assertEqual(profile.user, self.user)
        self.assertTrue(Portfolio.objects.filter(profile=profile).exists())
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.preferred_currency, "USD")

    def test_bootstrap_does_not_duplicate_objects(self):
        profile1 = bootstrap_user_profile_and_portfolio(self.user)
        profile2 = bootstrap_user_profile_and_portfolio(self.user)
        self.assertEqual(profile1.id, profile2.id)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Portfolio.objects.filter(profile=profile1).count(), 1)

    def test_bootstrap_with_custom_values(self):
        profile = bootstrap_user_profile_and_portfolio(
            self.user, country="IN", preferred_currency="INR"
        )
        self.assertEqual(profile.country, "IN")
        self.assertEqual(profile.preferred_currency, "INR")