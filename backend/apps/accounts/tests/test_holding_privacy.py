from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Account, AccountType, Holding
from accounts.services import HoldingService
from assets.models import AssetType
from assets.services import CustomAssetService
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class HoldingPrivacyTest(TestCase):
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

        self.user1 = User.objects.create_user(
            email="holding-owner-1@example.com",
            password="StrongPass123!",
        )
        self.user2 = User.objects.create_user(
            email="holding-owner-2@example.com",
            password="StrongPass123!",
        )
        ProfileBootstrapService.bootstrap(user=self.user1)
        ProfileBootstrapService.bootstrap(user=self.user2)

        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile

        self.portfolio1 = Portfolio.objects.get(profile=self.profile1, kind=Portfolio.Kind.PERSONAL)

        equity_type, _ = AssetType.objects.get_or_create(name="Equity", created_by=None)
        self.account_type = AccountType.objects.create(
            name="Holding Privacy Brokerage",
            slug="holding-privacy-brokerage",
            is_system=True,
        )
        self.account_type.allowed_asset_types.add(equity_type)

        self.account = Account.objects.create(
            portfolio=self.portfolio1,
            name="Owner1 Brokerage",
            account_type=self.account_type,
        )

        self.user2_custom_asset = CustomAssetService.create(
            profile=self.profile2,
            name="User2 Private Asset",
            asset_type_slug="equity",
            currency_code="USD",
        )

    def test_holding_service_rejects_other_users_private_asset(self):
        with self.assertRaises(ValidationError):
            HoldingService.create(
                account=self.account,
                asset=self.user2_custom_asset.asset,
                quantity="1",
            )

    def test_holding_model_rejects_other_users_private_asset(self):
        with self.assertRaises(ValidationError):
            Holding.objects.create(
                account=self.account,
                asset=self.user2_custom_asset.asset,
                quantity="1",
            )

    def test_manual_holding_defaults_to_manual_tracking_and_manual_price_for_custom_assets(self):
        custom_asset = CustomAssetService.create(
            profile=self.profile1,
            name="Owner1 Manual Asset",
            asset_type_slug="equity",
            currency_code="USD",
        ).asset

        holding = HoldingService.create(
            account=self.account,
            asset=custom_asset,
            quantity="2",
        )

        self.assertEqual(holding.tracking_mode, Holding.TrackingMode.MANUAL)
        self.assertEqual(holding.effective_tracking_mode, Holding.TrackingMode.MANUAL)
        self.assertEqual(holding.price_source_mode, Holding.PriceSourceMode.MANUAL)
        self.assertEqual(holding.effective_price_source_mode, Holding.PriceSourceMode.MANUAL)

