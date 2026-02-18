from django.test import TestCase

from accounts.models import Account, AccountType, BrokerageConnection
from accounts.services import BrokerageSyncService
from assets.models.core import AssetType
from assets.models.equity import EquityAsset
from assets.services.equity.equity_factory import EquityAssetFactory
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User

import uuid


class BrokerageSyncServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="brokerage-sync@example.com",
            password="StrongPass123!",
        )
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
        ProfileBootstrapService.bootstrap(user=self.user)

        self.profile = self.user.profile
        self.portfolio = Portfolio.objects.get(profile=self.profile, kind=Portfolio.Kind.PERSONAL)

        self.equity_type = AssetType.objects.get(slug="equity")
        self.usd = FXCurrency.objects.get(code="USD")

        self.account_type = AccountType.objects.create(
            name="Test Brokerage",
            slug="test-brokerage",
            is_system=True,
        )
        self.account_type.allowed_asset_types.add(self.equity_type)

        self.account = Account.objects.create(
            portfolio=self.portfolio,
            name="Brokerage Account",
            account_type=self.account_type,
        )
        self.connection = BrokerageConnection.objects.create(
            account=self.account,
            provider=BrokerageConnection.Provider.MANUAL,
            access_token_ref="manual:test",
        )

    def _equity(self, ticker: str):
        return EquityAssetFactory.create(
            snapshot_id=uuid.uuid4(),
            ticker=ticker,
            name=ticker,
            currency=self.usd,
        )

    def test_sync_from_payload_creates_holdings(self):
        self._equity("AAPL")
        self._equity("MSFT")

        summary = BrokerageSyncService.sync_from_payload(
            connection=self.connection,
            positions=[
                {"symbol": "AAPL", "quantity": "5", "average_cost": "100"},
                {"symbol": "MSFT", "quantity": "3", "average_cost": "200"},
            ],
            prune_missing=True,
        )

        self.assertEqual(summary["created"], 2)
        self.assertEqual(self.account.holdings.count(), 2)

