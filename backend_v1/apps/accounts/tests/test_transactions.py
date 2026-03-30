from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import Account, AccountTransaction, AccountType, Holding
from accounts.services import TransactionService
from assets.services import CustomAssetService
from assets.models import AssetType
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class TransactionServiceTest(TestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(
            slug="free",
            defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True},
        )

        AssetType.objects.get_or_create(name="Equity", created_by=None)

        self.user = User.objects.create_user(
            email="tx-test@example.com",
            password="StrongPass123!",
        )
        ProfileBootstrapService.bootstrap(user=self.user)
        self.profile = self.user.profile
        self.portfolio = Portfolio.objects.get(profile=self.profile, kind=Portfolio.Kind.PERSONAL)

        self.account_type = AccountType.objects.create(
            name="Ledger Brokerage",
            slug="ledger-brokerage",
            is_system=True,
        )
        self.account_type.allowed_asset_types.add(AssetType.objects.get(slug="equity"))

        self.account = Account.objects.create(
            portfolio=self.portfolio,
            name="Ledger Account",
            account_type=self.account_type,
            position_mode=Account.PositionMode.LEDGER,
        )

        self.asset = CustomAssetService.create(
            profile=self.profile,
            name="Private Equity",
            asset_type_slug="equity",
            currency_code="USD",
        ).asset

    def test_manual_buy_creates_transaction_and_holding(self):
        tx = TransactionService.create_manual(
            account=self.account,
            actor=self.user,
            event_type=AccountTransaction.EventType.BUY,
            traded_at=timezone.now(),
            quantity="10",
            unit_price="50",
            asset=self.asset,
        )
        self.assertEqual(tx.source, AccountTransaction.Source.MANUAL)
        holding = Holding.objects.get(account=self.account, asset=self.asset)
        self.assertEqual(holding.quantity, Decimal("10"))
        self.assertEqual(holding.tracking_mode, Holding.TrackingMode.TRACKED)
        self.assertEqual(holding.effective_tracking_mode, Holding.TrackingMode.TRACKED)

