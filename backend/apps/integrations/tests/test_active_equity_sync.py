from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.assets.models import Asset, AssetMarketData, AssetType
from apps.integrations.models import ActiveEquityListing
from apps.integrations.services import (
    ActiveEquityAssetService,
    ActiveEquitySyncService,
    HeldEquityReviewService,
)


class ActiveEquitySyncServiceTests(TestCase):
    @patch("apps.integrations.services.active_equity_sync_service.FMP_PROVIDER.get_actively_traded_rows")
    def test_refresh_rebuilds_current_active_list(self, mock_get_rows):
        mock_get_rows.return_value = [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corp."},
        ]

        result = ActiveEquitySyncService.refresh_from_fmp()

        self.assertEqual(result["row_count"], 2)
        self.assertEqual(ActiveEquityListing.objects.count(), 2)

        mock_get_rows.return_value = [{"symbol": "NVDA", "name": "NVIDIA Corporation"}]
        ActiveEquitySyncService.refresh_from_fmp()

        self.assertEqual(ActiveEquityListing.objects.count(), 1)
        self.assertTrue(ActiveEquityListing.objects.filter(symbol="NVDA").exists())


class HeldEquityReviewServiceTests(TestCase):
    def setUp(self):
        self.equity_type = AssetType.objects.create(name="Equity")

    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.get_profile_with_identifiers")
    def test_enrich_identity_stores_identifiers_on_market_data(self, mock_get_profile):
        asset = Asset.objects.create(asset_type=self.equity_type, name="Apple Inc.", symbol="AAPL")
        mock_get_profile.return_value = {
            "company": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "currency": "USD",
                "exchange": "NASDAQ",
                "country": "US",
                "sector": "Technology",
                "industry": "Consumer Electronics",
            },
            "identifiers": {
                "isin": "US0378331005",
                "cusip": "037833100",
                "cik": "320193",
            },
        }

        market_data = HeldEquityReviewService.enrich_identity(asset=asset)

        self.assertEqual(market_data.isin, "US0378331005")
        self.assertEqual(market_data.cusip, "037833100")
        self.assertEqual(market_data.cik, "320193")
        self.assertEqual(market_data.status, AssetMarketData.Status.TRACKED)

    def test_review_marks_asset_for_review_when_symbol_missing_and_no_identifiers(self):
        asset = Asset.objects.create(asset_type=self.equity_type, name="Facebook", symbol="FB")
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="FB",
            last_seen_name="Facebook",
            status=AssetMarketData.Status.TRACKED,
        )

        result = HeldEquityReviewService.review_asset(asset=asset)

        asset.refresh_from_db()
        self.assertEqual(result, "needs_review")
        self.assertEqual(asset.market_data.status, AssetMarketData.Status.NEEDS_REVIEW)


class ActiveEquityAssetServiceTests(TestCase):
    def setUp(self):
        self.equity_type = AssetType.objects.create(name="Equity")
        self.user = get_user_model().objects.create_user(
            email="equity-picker@example.com",
            password="StrongPass123!",
        )
        ActiveEquityListing.objects.create(symbol="AAPL", name="Apple Inc.")

    def test_get_or_create_public_asset_creates_shared_equity_asset(self):
        asset = ActiveEquityAssetService.get_or_create_public_asset(symbol="aapl")

        self.assertIsNone(asset.owner)
        self.assertEqual(asset.symbol, "AAPL")
        self.assertEqual(asset.name, "Apple Inc.")
        self.assertEqual(asset.market_data.provider_symbol, "AAPL")
        self.assertEqual(asset.market_data.status, AssetMarketData.Status.TRACKED)

    def test_get_or_create_public_asset_reuses_consistent_existing_asset(self):
        asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Apple Inc.",
            symbol="AAPL",
        )

        reused = ActiveEquityAssetService.get_or_create_public_asset(symbol="AAPL")

        self.assertEqual(reused.pk, asset.pk)

    @patch("apps.integrations.services.active_equity_asset_service.HeldEquityReviewService.enrich_identity")
    def test_ensure_identity_only_fetches_profile_until_identifiers_exist(self, mock_enrich_identity):
        asset = Asset.objects.create(
            asset_type=self.equity_type,
            name="Apple Inc.",
            symbol="AAPL",
        )
        market_data = AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="AAPL",
            status=AssetMarketData.Status.TRACKED,
        )
        mock_enrich_identity.return_value = market_data

        ActiveEquityAssetService.ensure_identity_for_held_asset(asset=asset)
        ActiveEquityAssetService.ensure_identity_for_held_asset(asset=asset)

        self.assertEqual(mock_enrich_identity.call_count, 2)

        market_data.isin = "US0378331005"
        market_data.save()

        ActiveEquityAssetService.ensure_identity_for_held_asset(asset=asset)

        self.assertEqual(mock_enrich_identity.call_count, 2)


class ActiveEquityApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="active-equity-api@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(self.user)
        ActiveEquityListing.objects.create(symbol="AAPL", name="Apple Inc.")
        ActiveEquityListing.objects.create(symbol="MSFT", name="Microsoft Corporation")

    def test_active_equity_search_returns_filtered_results(self):
        response = self.client.get(reverse("active-equity-list"), {"q": "app"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"symbol": "AAPL", "name": "Apple Inc."}])
