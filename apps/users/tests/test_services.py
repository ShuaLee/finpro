"""
users.tests.test_services
~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for user service functions like bootstrap_user_profile_and_portfolio.
"""

from django.test import TestCase
from users.models import User, Profile
from portfolios.models import Portfolio
from subscriptions.models import Plan
from users.services import bootstrap_user_profile_and_portfolio


class UserServicesTests(TestCase):
    def setUp(self):
        # Create user and Free plan
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass")
        self.free_plan = Plan.objects.create(
            name="Free",
            slug="free",
            description="Free plan",
            max_stocks=10,
            allow_crypto=False,
            allow_metals=False,
            price_per_month=0
        )

    def test_bootstrap_assigns_free_plan_and_portfolio(self):
        """
        Ensure bootstrap:
        - Creates Profile
        - Assigns Free plan
        - Creates Portfolio
        """
        profile = bootstrap_user_profile_and_portfolio(self.user)
        self.assertEqual(profile.plan.slug, "free")
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.preferred_currency, "USD")

        portfolio = Portfolio.objects.get(profile=profile)
        self.assertIsNotNone(portfolio)

    def test_bootstrap_is_idempotent(self):
        """
        Ensure calling bootstrap twice does not duplicate Profile or Portfolio.
        """
        profile1 = bootstrap_user_profile_and_portfolio(self.user)
        profile2 = bootstrap_user_profile_and_portfolio(self.user)

        self.assertEqual(profile1.id, profile2.id)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Portfolio.objects.filter(profile=profile1).count(), 1)

    def test_bootstrap_respects_custom_country_and_currency(self):
        """
        Ensure bootstrap uses provided country and currency instead of defaults.
        """
        profile = bootstrap_user_profile_and_portfolio(
            self.user, country="CA", preferred_currency="CAD")
        self.assertEqual(profile.country, "CA")
        self.assertEqual(profile.preferred_currency, "CAD")
