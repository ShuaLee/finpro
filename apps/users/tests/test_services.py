"""
users.tests.test_services
~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for user service functions like bootstrap_user_profile_and_portfolio.
"""

from django.test import TestCase
from users.models import User, Profile
from portfolios.models import Portfolio
from subscriptions.models import Plan, AccountType
from users.services import bootstrap_user_profile_and_portfolio


class UserServicesTests(TestCase):
    """
    Tests the behavior of user-related service functions that handle
    automatic setup of Profile, Plan, and Portfolio for new users.
    """

    def setUp(self):
        """
        Create a test user, Free plan, and Individual account type for bootstrap logic.
        """
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass", is_over_13=True
        )
        self.free_plan = Plan.objects.create(
            name="Free",
            slug="free",
            description="Free plan",
            max_stocks=10,
            allow_crypto=False,
            allow_metals=False,
            price_per_month=0,
            is_active=True,
        )
        self.account_type = AccountType.objects.create(
            name="Individual Investor",
            slug="individual",
            description="Default account type for personal investors"
        )

    def test_bootstrap_creates_profile_and_assigns_defaults(self):
        """
        Ensure bootstrap:
        - Creates Profile if missing.
        - Assigns Free plan.
        - Assigns Individual account type.
        - Sets default country and currency (US, USD).
        - Creates Portfolio for the profile.
        """
        profile = bootstrap_user_profile_and_portfolio(self.user)

        # Validate Profile defaults
        self.assertEqual(profile.plan.slug, "free")
        self.assertEqual(profile.account_type.slug, "individual")
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.preferred_currency, "USD")

        # Validate Portfolio creation
        portfolio = Portfolio.objects.get(profile=profile)
        self.assertIsNotNone(portfolio)

    def test_bootstrap_is_idempotent(self):
        """
        Ensure calling bootstrap multiple times:
        - Does not duplicate Profile.
        - Does not duplicate Portfolio.
        """
        profile1 = bootstrap_user_profile_and_portfolio(self.user)
        profile2 = bootstrap_user_profile_and_portfolio(self.user)

        # Validate no duplicates
        self.assertEqual(profile1.id, profile2.id)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Portfolio.objects.filter(profile=profile1).count(), 1)