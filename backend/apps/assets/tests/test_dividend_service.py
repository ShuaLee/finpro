from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.assets.models import Asset, AssetDividendSnapshot, AssetMarketData, AssetPrice, AssetType
from apps.assets.services import AssetDividendService


class AssetDividendServiceTests(TestCase):
    def setUp(self):
        self.equity_type = AssetType.objects.create(name="Equity")
        self.asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Apple Inc.",
            symbol="AAPL",
        )
        AssetMarketData.objects.create(
            asset=self.asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="AAPL",
            status=AssetMarketData.Status.TRACKED,
        )
        AssetPrice.objects.create(
            asset=self.asset,
            price=Decimal("200"),
            source="FMP",
        )

    @patch("apps.assets.services.asset_dividend_service.FMP_PROVIDER.get_dividends")
    def test_sync_creates_inactive_snapshot_when_no_dividend_events(self, mock_get_dividends):
        mock_get_dividends.return_value = []

        snapshot = AssetDividendService.sync(self.asset)

        self.assertEqual(snapshot.status, AssetDividendSnapshot.DividendStatus.INACTIVE)
        self.assertEqual(snapshot.trailing_12m_dividend, Decimal("0"))

    @patch("apps.assets.services.asset_dividend_service.FMP_PROVIDER.get_dividends")
    def test_sync_computes_trailing_forward_and_yields(self, mock_get_dividends):
        mock_get_dividends.return_value = [
            {"date": date(2026, 3, 1), "dividend": "0.25", "frequency": "Quarterly"},
            {"date": date(2025, 12, 1), "dividend": "0.25", "frequency": "Quarterly"},
            {"date": date(2025, 9, 1), "dividend": "0.25", "frequency": "Quarterly"},
            {"date": date(2025, 6, 1), "dividend": "0.25", "frequency": "Quarterly"},
        ]

        snapshot = AssetDividendService.sync(self.asset)

        self.assertEqual(snapshot.status, AssetDividendSnapshot.DividendStatus.CONFIDENT)
        self.assertEqual(snapshot.cadence_status, AssetDividendSnapshot.CadenceStatus.ACTIVE)
        self.assertEqual(snapshot.trailing_12m_dividend, Decimal("1.00"))
        self.assertEqual(snapshot.forward_annual_dividend, Decimal("1.00"))
        self.assertEqual(snapshot.trailing_dividend_yield, Decimal("0.005"))
        self.assertEqual(snapshot.forward_dividend_yield, Decimal("0.005"))
