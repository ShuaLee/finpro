from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Account, AccountType, Holding
from assets.models import Asset, AssetType
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class AccountRestrictionTests(TestCase):
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
            defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True},
        )

        self.user = User.objects.create_user(
            email="account-restrictions@example.com",
            password="StrongPass123!",
        )
        ProfileBootstrapService.bootstrap(user=self.user)
        self.profile = self.user.profile
        self.portfolio = Portfolio.objects.get(profile=self.profile, kind=Portfolio.Kind.PERSONAL)

        self.equity_type = AssetType.objects.create(name="Equity", created_by=None)
        self.crypto_type = AssetType.objects.create(name="Cryptocurrency", created_by=None)

        self.account_type = AccountType.objects.create(
            name="Restriction Test Brokerage",
            slug="restriction-test-brokerage",
            is_system=True,
        )
        self.account_type.allowed_asset_types.add(self.equity_type)

        self.equity_asset = Asset.objects.create(asset_type=self.equity_type)
        self.crypto_asset = Asset.objects.create(asset_type=self.crypto_type)

    def test_account_inherits_account_type_restrictions_on_create(self):
        account = Account.objects.create(
            portfolio=self.portfolio,
            name="Main Brokerage",
            account_type=self.account_type,
        )

        self.assertFalse(account.enforce_restrictions)
        self.assertEqual(
            list(account.allowed_asset_types.values_list("slug", flat=True)),
            [self.equity_type.slug],
        )

    def test_holding_blocks_disallowed_asset_when_restrictions_enforced(self):
        account = Account.objects.create(
            portfolio=self.portfolio,
            name="Restricted Brokerage",
            account_type=self.account_type,
        )
        account.enforce_restrictions = True
        account.save(update_fields=["enforce_restrictions"])

        with self.assertRaises(ValidationError):
            Holding.objects.create(
                account=account,
                asset=self.crypto_asset,
                quantity="1",
            )

    def test_holding_allows_disallowed_asset_when_restrictions_not_enforced(self):
        account = Account.objects.create(
            portfolio=self.portfolio,
            name="Flexible Brokerage",
            account_type=self.account_type,
        )
        account.enforce_restrictions = False
        account.save(update_fields=["enforce_restrictions"])

        holding = Holding.objects.create(
            account=account,
            asset=self.crypto_asset,
            quantity="1",
        )

        self.assertEqual(holding.asset_id, self.crypto_asset.id)
