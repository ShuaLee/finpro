from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.assets.models import Asset, AssetPrice, AssetType
from apps.assets.services import AssetPriceService
from apps.integrations.exceptions import IntegrationError


@override_settings(ASSET_PRICE_CACHE_TTL_SECONDS=600)
class AssetPriceServiceTests(TestCase):
    def setUp(self):
        self.equity_type = AssetType.objects.create(name="Equity")
        self.asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Apple Inc.",
            symbol="AAPL",
        )

    @patch("apps.assets.services.asset_price_service.PublicAssetSyncService.refresh_quote")
    def test_get_current_price_uses_cached_price_when_fresh(self, mock_refresh_quote):
        price = AssetPrice.objects.create(
            asset=self.asset,
            price=Decimal("210.15"),
            change=Decimal("1.25"),
            volume=100,
            source="FMP",
        )

        result = AssetPriceService.get_current_price(asset=self.asset)

        self.assertEqual(result.pk, price.pk)
        mock_refresh_quote.assert_not_called()

    @patch("apps.assets.services.asset_price_service.PublicAssetSyncService.refresh_quote")
    def test_get_current_price_refreshes_when_cache_is_stale(self, mock_refresh_quote):
        AssetPrice.objects.create(
            asset=self.asset,
            price=Decimal("210.15"),
            change=Decimal("1.25"),
            volume=100,
            source="FMP",
        )
        stale_time = timezone.now() - timedelta(minutes=11)
        AssetPrice.objects.filter(asset=self.asset).update(as_of=stale_time)
        self.asset.refresh_from_db()
        refreshed_price = AssetPrice.objects.get(asset=self.asset)
        mock_refresh_quote.return_value = refreshed_price

        result = AssetPriceService.get_current_price(asset=self.asset)

        self.assertEqual(result.pk, refreshed_price.pk)
        mock_refresh_quote.assert_called_once_with(asset=self.asset)

    @patch("apps.assets.services.asset_price_service.PublicAssetSyncService.refresh_quote")
    def test_get_current_price_refreshes_when_forced(self, mock_refresh_quote):
        price = AssetPrice.objects.create(
            asset=self.asset,
            price=Decimal("210.15"),
            change=Decimal("1.25"),
            volume=100,
            source="FMP",
        )
        mock_refresh_quote.return_value = price

        AssetPriceService.get_current_price(asset=self.asset, force_refresh=True)

        mock_refresh_quote.assert_called_once_with(asset=self.asset)

    @patch("apps.assets.services.asset_price_service.PublicAssetSyncService.refresh_quote")
    def test_get_current_price_returns_stale_cache_when_refresh_fails(self, mock_refresh_quote):
        price = AssetPrice.objects.create(
            asset=self.asset,
            price=Decimal("210.15"),
            change=Decimal("1.25"),
            volume=100,
            source="FMP",
        )
        stale_time = timezone.now() - timedelta(minutes=11)
        AssetPrice.objects.filter(asset=self.asset).update(as_of=stale_time)
        self.asset.refresh_from_db()
        mock_refresh_quote.side_effect = IntegrationError("Temporary outage")

        result = AssetPriceService.get_current_price(asset=self.asset)

        self.assertEqual(result.pk, price.pk)
        mock_refresh_quote.assert_called_once_with(asset=self.asset)

    def test_asset_reports_price_freshness(self):
        AssetPrice.objects.create(
            asset=self.asset,
            price=Decimal("210.15"),
            change=Decimal("1.25"),
            volume=100,
            source="FMP",
        )

        self.asset.refresh_from_db()
        self.assertTrue(self.asset.current_price_is_fresh)

        stale_time = timezone.now() - timedelta(minutes=11)
        AssetPrice.objects.filter(asset=self.asset).update(as_of=stale_time)
        self.asset.refresh_from_db()
        self.assertFalse(self.asset.current_price_is_fresh)
