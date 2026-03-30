from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Account, AccountType
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class OwnershipImmutabilityTest(TestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(
            code="USD",
            defaults={"name": "US Dollar", "is_active": True},
        )
        Country.objects.get_or_create(
            code="US",
            defaults={"name": "United States", "is_active": True},
        )
        Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free",
                "tier": Plan.Tier.FREE,
                "is_active": True,
            },
        )

        self.user_a = User.objects.create_user(
            email="immutable-a@example.com",
            password="StrongPass123!",
        )
        self.user_b = User.objects.create_user(
            email="immutable-b@example.com",
            password="StrongPass123!",
        )

        ProfileBootstrapService.bootstrap(user=self.user_a)
        ProfileBootstrapService.bootstrap(user=self.user_b)

        self.profile_a = self.user_a.profile
        self.profile_b = self.user_b.profile

        self.portfolio_a = Portfolio.objects.get(profile=self.profile_a, kind=Portfolio.Kind.PERSONAL)
        self.portfolio_b = Portfolio.objects.get(profile=self.profile_b, kind=Portfolio.Kind.PERSONAL)

        self.account_type = AccountType.objects.create(
            name="Immutable Brokerage",
            slug="immutable-brokerage",
            is_system=True,
        )
        self.account = Account.objects.create(
            portfolio=self.portfolio_a,
            name="Primary Account",
            account_type=self.account_type,
        )

    def test_profile_owner_cannot_be_reassigned(self):
        self.profile_a.user = self.user_b
        with self.assertRaises(ValidationError):
            self.profile_a.save()

    def test_portfolio_owner_cannot_be_reassigned(self):
        self.portfolio_a.profile = self.profile_b
        with self.assertRaises(ValidationError):
            self.portfolio_a.save()

    def test_account_portfolio_cannot_be_reassigned(self):
        self.account.portfolio = self.portfolio_b
        with self.assertRaises(ValidationError):
            self.account.save()

