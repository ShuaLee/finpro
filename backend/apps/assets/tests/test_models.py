from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.assets.models import Asset, AssetDividendSnapshot, AssetMarketData, AssetType


class AssetTypeModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="assets@example.com",
            password="StrongPass123!",
        )
        self.profile = self.user.profile

    def test_system_asset_type_slug_is_normalized(self):
        asset_type = AssetType.objects.create(name="Private Equity")

        self.assertEqual(asset_type.slug, "private_equity")
        self.assertTrue(asset_type.is_system)

    def test_custom_asset_type_cannot_reuse_system_name(self):
        AssetType.objects.create(name="Equity")

        asset_type = AssetType(
            name="Equity",
            created_by=self.profile,
        )

        with self.assertRaises(ValidationError):
            asset_type.full_clean()


class AssetModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="assets-owner@example.com",
            password="StrongPass123!",
        )
        self.profile = self.user.profile
        self.equity_type = AssetType.objects.create(name="Equity")
        self.crypto_type = AssetType.objects.create(name="Cryptocurrency")

    def test_public_asset_symbol_is_normalized_to_uppercase(self):
        asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Apple Inc.",
            symbol="aapl",
        )

        self.assertEqual(asset.symbol, "AAPL")
        self.assertTrue(asset.is_public)

    def test_public_asset_cannot_be_reassigned_or_retyped(self):
        asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Apple Inc.",
            symbol="AAPL",
        )

        asset.owner = self.profile
        with self.assertRaises(ValidationError):
            asset.full_clean()

        asset.refresh_from_db()
        asset.asset_type = self.crypto_type
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_private_asset_name_must_be_unique_per_owner_and_type(self):
        Asset.objects.create(
            asset_type=self.equity_type,
            owner=self.profile,
            name="My Private Position",
        )

        duplicate = Asset(
            asset_type=self.equity_type,
            owner=self.profile,
            name="My Private Position",
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_asset_can_report_market_tracking_state(self):
        asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Apple Inc.",
            symbol="AAPL",
        )

        self.assertFalse(asset.is_market_tracked)

        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="AAPL",
            status=AssetMarketData.Status.TRACKED,
        )

        asset.refresh_from_db()
        self.assertTrue(asset.is_market_tracked)


class AssetMarketDataModelTests(TestCase):
    def setUp(self):
        self.equity_type = AssetType.objects.create(name="Equity")

    def test_tracked_market_data_requires_provider_symbol(self):
        asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Test Asset",
        )

        market_data = AssetMarketData(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            status=AssetMarketData.Status.TRACKED,
        )

        with self.assertRaises(ValidationError):
            market_data.full_clean()


class AssetDividendSnapshotModelTests(TestCase):
    def setUp(self):
        self.equity_type = AssetType.objects.create(name="Equity")
        self.crypto_type = AssetType.objects.create(name="Cryptocurrency")

    def test_dividend_snapshot_requires_equity_asset_type(self):
        asset = Asset.objects.create(
            asset_type=self.crypto_type,
            name="Bitcoin",
            symbol="BTCUSD",
        )

        snapshot = AssetDividendSnapshot(asset=asset)

        with self.assertRaises(ValidationError):
            snapshot.full_clean()
