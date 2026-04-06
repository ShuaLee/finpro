from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.assets.models import Asset, AssetMarketData, AssetPrice, AssetType
from apps.assets.services import PublicAssetSyncService
from apps.integrations.exceptions import EmptyProviderResult
from apps.integrations.shared.types import CompanyProfile, QuoteSnapshot


class PublicAssetSyncServiceTests(TestCase):
    def setUp(self):
        self.equity_type = AssetType.objects.create(name="Equity")

    @patch("apps.assets.services.public_asset_sync_service.FMP_PROVIDER.get_company_profile")
    def test_sync_symbol_creates_public_asset_and_market_data(self, mock_get_company_profile):
        mock_get_company_profile.return_value = CompanyProfile(
            symbol="AAPL",
            name="Apple Inc.",
            currency="USD",
            exchange="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            country="US",
            website="https://apple.com",
            description="Maker of iPhones",
            image_url="https://example.com/aapl.png",
        )

        asset = PublicAssetSyncService.sync_symbol(symbol="aapl", asset_type_slug="equity")

        self.assertEqual(asset.symbol, "AAPL")
        self.assertIsNone(asset.owner)
        self.assertEqual(asset.market_data.status, AssetMarketData.Status.TRACKED)
        self.assertEqual(asset.market_data.provider_symbol, "AAPL")
        self.assertEqual(asset.data["market_profile"]["exchange"], "NASDAQ")

    @patch("apps.assets.services.public_asset_sync_service.FMP_PROVIDER.get_quote")
    def test_refresh_quote_updates_asset_price_and_tracking_state(self, mock_get_quote):
        asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Apple Inc.",
            symbol="AAPL",
        )
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="AAPL",
            status=AssetMarketData.Status.STALE,
        )
        mock_get_quote.return_value = QuoteSnapshot(
            symbol="AAPL",
            price=Decimal("210.15"),
            change=Decimal("1.50"),
            volume=1000,
            source="FMP",
        )

        price = PublicAssetSyncService.refresh_quote(asset=asset)

        self.assertEqual(price.price, Decimal("210.15"))
        self.assertEqual(price.source, "FMP")
        asset.refresh_from_db()
        self.assertEqual(asset.market_data.status, AssetMarketData.Status.TRACKED)

    @patch("apps.assets.services.public_asset_sync_service.FMP_PROVIDER.get_quote")
    def test_refresh_quotes_marks_assets_stale_when_provider_returns_empty(self, mock_get_quote):
        asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Old Co",
            symbol="OLD",
        )
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="OLD",
            status=AssetMarketData.Status.TRACKED,
        )
        mock_get_quote.side_effect = EmptyProviderResult("No quote found for OLD.")

        result = PublicAssetSyncService.refresh_quotes_for_assets(assets=[asset])

        self.assertEqual(result["stale"], 1)
        asset.refresh_from_db()
        self.assertFalse(asset.is_active)
        self.assertEqual(asset.market_data.status, AssetMarketData.Status.STALE)
        self.assertIn("No quote found", asset.market_data.last_error)

    @patch("apps.assets.services.public_asset_sync_service.FMP_PROVIDER.get_quote")
    def test_refresh_quote_creates_price_cache_row(self, mock_get_quote):
        asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="MSFT",
            symbol="MSFT",
        )
        mock_get_quote.return_value = QuoteSnapshot(
            symbol="MSFT",
            price=Decimal("100"),
            change=Decimal("0.5"),
            volume=10,
            source="FMP",
        )

        PublicAssetSyncService.refresh_quote(asset=asset)

        self.assertTrue(AssetPrice.objects.filter(asset=asset).exists())

    @patch("apps.assets.services.public_asset_sync_service.FMP_PROVIDER.get_actively_traded_symbols")
    @patch("apps.assets.services.public_asset_sync_service.FMP_PROVIDER.get_stock_list")
    def test_sync_equity_directory_uses_stock_list_and_active_symbols(
        self,
        mock_get_stock_list,
        mock_get_actively_traded_symbols,
    ):
        mock_get_stock_list.return_value = [
            {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "currency": "USD"},
            {"symbol": "OLD", "name": "Old Co", "exchange": "NYSE", "currency": "USD"},
        ]
        mock_get_actively_traded_symbols.return_value = {"AAPL"}

        result = PublicAssetSyncService.sync_equity_directory()

        self.assertEqual(result["created"], 2)
        aapl = Asset.objects.get(symbol="AAPL")
        old = Asset.objects.get(symbol="OLD")
        self.assertTrue(aapl.is_active)
        self.assertFalse(old.is_active)
        self.assertEqual(aapl.market_data.status, AssetMarketData.Status.TRACKED)
        self.assertEqual(old.market_data.status, AssetMarketData.Status.STALE)
