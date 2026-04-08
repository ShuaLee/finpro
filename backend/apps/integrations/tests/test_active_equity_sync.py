from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.assets.models import Asset, AssetMarketData, AssetType
from apps.integrations.models import ActiveCommodityListing, ActiveCryptoListing, ActiveEquityListing
from apps.integrations.services import (
    ActiveCommodityAssetService,
    ActiveCommoditySyncService,
    ActiveCryptoAssetService,
    ActiveCryptoSyncService,
    ActiveEquityAssetService,
    ActiveEquitySyncService,
    HeldEquityReviewService,
    HeldMarketAssetReviewService,
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
        self.assertEqual(mock_get_rows.call_count, 1)

        mock_get_rows.return_value = [{"symbol": "NVDA", "name": "NVIDIA Corporation"}]
        ActiveEquitySyncService.refresh_from_fmp()

        self.assertEqual(ActiveEquityListing.objects.count(), 1)
        self.assertTrue(ActiveEquityListing.objects.filter(symbol="NVDA").exists())
        self.assertEqual(mock_get_rows.call_count, 2)

    @patch("apps.integrations.services.active_crypto_sync_service.FMP_PROVIDER.get_cryptocurrency_rows")
    def test_crypto_refresh_rebuilds_current_crypto_list(self, mock_get_rows):
        mock_get_rows.return_value = [
            {"symbol": "BTCUSD", "name": "Bitcoin", "base_symbol": "BTC", "quote_currency": "USD"},
            {"symbol": "ETHUSD", "name": "Ethereum", "base_symbol": "ETH", "quote_currency": "USD"},
        ]

        result = ActiveCryptoSyncService.refresh_from_fmp()

        self.assertEqual(result["row_count"], 2)
        self.assertEqual(ActiveCryptoListing.objects.count(), 2)
        self.assertEqual(mock_get_rows.call_count, 1)

    @patch("apps.integrations.services.active_commodity_sync_service.FMP_PROVIDER.get_commodity_rows")
    def test_commodity_refresh_rebuilds_current_commodity_list(self, mock_get_rows):
        mock_get_rows.return_value = [
            {"symbol": "GCUSD", "name": "Gold", "exchange": "COMEX", "trade_month": "", "currency": "USD"},
            {"symbol": "CLUSD", "name": "Crude Oil", "exchange": "NYMEX", "trade_month": "", "currency": "USD"},
        ]

        result = ActiveCommoditySyncService.refresh_from_fmp()

        self.assertEqual(result["row_count"], 2)
        self.assertEqual(ActiveCommodityListing.objects.count(), 2)
        self.assertEqual(mock_get_rows.call_count, 1)


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
        self.assertEqual(mock_get_profile.call_count, 1)

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

    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_cik")
    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_cusip")
    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_isin")
    def test_review_resolves_ticker_change_by_identifier_when_symbol_missing(
        self,
        mock_search_by_isin,
        mock_search_by_cusip,
        mock_search_by_cik,
    ):
        ActiveEquityListing.objects.create(symbol="META", name="Meta Platforms, Inc.")
        asset = Asset.objects.create(asset_type=self.equity_type, name="Facebook, Inc.", symbol="FB")
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="FB",
            last_seen_symbol="FB",
            last_seen_name="Facebook, Inc.",
            last_seen_exchange="NASDAQ",
            isin="US30303M1027",
            status=AssetMarketData.Status.TRACKED,
        )
        mock_search_by_isin.return_value = [
            {
                "symbol": "META",
                "name": "Meta Platforms, Inc.",
                "exchange": "NASDAQ",
                "isin": "US30303M1027",
                "cusip": "30303M102",
                "cik": "1326801",
            }
        ]
        mock_search_by_cusip.return_value = []
        mock_search_by_cik.return_value = []

        result = HeldEquityReviewService.review_asset(asset=asset)

        asset.refresh_from_db()
        self.assertEqual(result, "tracked")
        self.assertEqual(asset.symbol, "META")
        self.assertEqual(asset.name, "Meta Platforms, Inc.")
        self.assertEqual(asset.market_data.provider_symbol, "META")
        self.assertEqual(asset.market_data.status, AssetMarketData.Status.TRACKED)
        self.assertEqual(mock_search_by_isin.call_count, 1)
        self.assertEqual(mock_search_by_cusip.call_count, 0)
        self.assertEqual(mock_search_by_cik.call_count, 0)

    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_cik")
    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_cusip")
    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_isin")
    def test_review_resolves_same_symbol_name_change_conflict_using_identifiers(
        self,
        mock_search_by_isin,
        mock_search_by_cusip,
        mock_search_by_cik,
    ):
        ActiveEquityListing.objects.create(symbol="FB", name="FB Newsite Corp")
        ActiveEquityListing.objects.create(symbol="META", name="Meta Platforms, Inc.")
        asset = Asset.objects.create(asset_type=self.equity_type, name="Facebook, Inc.", symbol="FB")
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="FB",
            last_seen_symbol="FB",
            last_seen_name="Facebook, Inc.",
            last_seen_exchange="NASDAQ",
            isin="US30303M1027",
            status=AssetMarketData.Status.TRACKED,
        )
        mock_search_by_isin.return_value = [
            {
                "symbol": "FB",
                "name": "FB Newsite Corp",
                "exchange": "NASDAQ",
                "isin": "US0000000001",
                "cusip": "000000001",
                "cik": "1",
            },
            {
                "symbol": "META",
                "name": "Meta Platforms, Inc.",
                "exchange": "NASDAQ",
                "isin": "US30303M1027",
                "cusip": "30303M102",
                "cik": "1326801",
            },
        ]
        mock_search_by_cusip.return_value = []
        mock_search_by_cik.return_value = []

        result = HeldEquityReviewService.review_asset(asset=asset)

        asset.refresh_from_db()
        self.assertEqual(result, "tracked")
        self.assertEqual(asset.symbol, "META")
        self.assertEqual(asset.market_data.provider_symbol, "META")
        self.assertEqual(mock_search_by_isin.call_count, 1)
        self.assertEqual(mock_search_by_cusip.call_count, 0)
        self.assertEqual(mock_search_by_cik.call_count, 0)

    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_cik")
    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_cusip")
    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_isin")
    def test_review_marks_stale_when_identifier_candidates_are_not_clear_active_match(
        self,
        mock_search_by_isin,
        mock_search_by_cusip,
        mock_search_by_cik,
    ):
        ActiveEquityListing.objects.create(symbol="METAA", name="Meta Holdings A")
        ActiveEquityListing.objects.create(symbol="METAB", name="Meta Holdings B")
        asset = Asset.objects.create(asset_type=self.equity_type, name="Meta Holdings", symbol="META")
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="META",
            last_seen_symbol="META",
            last_seen_name="Meta Holdings",
            last_seen_exchange="NASDAQ",
            isin="US9999999999",
            status=AssetMarketData.Status.TRACKED,
        )
        mock_search_by_isin.return_value = [
            {
                "symbol": "METAA",
                "name": "Meta Holdings A",
                "exchange": "NASDAQ",
                "isin": "US9999999999",
                "cusip": "999999991",
                "cik": "11",
            },
            {
                "symbol": "METAB",
                "name": "Meta Holdings B",
                "exchange": "NASDAQ",
                "isin": "US9999999999",
                "cusip": "999999992",
                "cik": "12",
            },
        ]
        mock_search_by_cusip.return_value = []
        mock_search_by_cik.return_value = []

        result = HeldEquityReviewService.review_asset(asset=asset)

        asset.refresh_from_db()
        self.assertEqual(result, "stale")
        self.assertFalse(asset.is_active)
        self.assertEqual(asset.market_data.status, AssetMarketData.Status.STALE)
        self.assertEqual(mock_search_by_isin.call_count, 1)
        self.assertEqual(mock_search_by_cusip.call_count, 0)
        self.assertEqual(mock_search_by_cik.call_count, 0)


class ActiveEquityAssetServiceTests(TestCase):
    def setUp(self):
        self.equity_type = AssetType.objects.create(name="Equity")
        self.crypto_type = AssetType.objects.create(name="Cryptocurrency")
        self.commodity_type = AssetType.objects.create(name="Commodity")
        self.precious_metal_type = AssetType.objects.create(name="Precious Metal")
        self.user = get_user_model().objects.create_user(
            email="equity-picker@example.com",
            password="StrongPass123!",
        )
        ActiveEquityListing.objects.create(symbol="AAPL", name="Apple Inc.")
        ActiveCryptoListing.objects.create(
            symbol="BTCUSD",
            name="Bitcoin",
            base_symbol="BTC",
            quote_currency="USD",
        )
        ActiveCommodityListing.objects.create(
            symbol="GCUSD",
            name="Gold",
            exchange="COMEX",
            trade_month="",
            currency="USD",
        )

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

    def test_crypto_asset_service_promotes_active_crypto_listing(self):
        asset = ActiveCryptoAssetService.get_or_create_public_asset(symbol="btcusd")

        self.assertIn(asset.asset_type.slug, {"crypto", "cryptocurrency"})
        self.assertEqual(asset.symbol, "BTCUSD")
        self.assertEqual(asset.market_data.provider_symbol, "BTCUSD")
        self.assertEqual(asset.data["crypto_profile"]["base_symbol"], "BTC")

    def test_precious_metal_asset_service_derives_asset_from_commodity_listing(self):
        asset = ActiveCommodityAssetService.get_or_create_precious_metal_asset(metal="gold")

        self.assertEqual(asset.asset_type.slug, "precious_metal")
        self.assertEqual(asset.name, "Gold")
        self.assertEqual(asset.symbol, "GCUSD")
        self.assertEqual(asset.market_data.provider_symbol, "GCUSD")


class HeldMarketAssetReviewServiceTests(TestCase):
    def setUp(self):
        self.crypto_type = AssetType.objects.create(name="Cryptocurrency")
        self.commodity_type = AssetType.objects.create(name="Commodity")
        self.precious_metal_type = AssetType.objects.create(name="Precious Metal")

    def test_review_marks_crypto_stale_when_pair_disappears(self):
        asset = Asset.objects.create(asset_type=self.crypto_type, name="Bitcoin", symbol="BTCUSD")
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="BTCUSD",
            status=AssetMarketData.Status.TRACKED,
        )

        result = HeldMarketAssetReviewService.review_asset(asset=asset)

        self.assertEqual(result, "stale")
        asset.refresh_from_db()
        self.assertFalse(asset.is_active)

    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_isin")
    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.get_profile_with_identifiers")
    def test_review_market_crypto_uses_local_active_list_only_and_no_identifier_calls(
        self,
        mock_get_profile,
        mock_search_by_isin,
    ):
        ActiveCryptoListing.objects.create(
            symbol="BTCUSD",
            name="Bitcoin",
            base_symbol="BTC",
            quote_currency="USD",
        )
        asset = Asset.objects.create(asset_type=self.crypto_type, name="Bitcoin", symbol="BTCUSD")
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="BTCUSD",
            status=AssetMarketData.Status.TRACKED,
        )

        result = HeldMarketAssetReviewService.review_asset(asset=asset)

        self.assertEqual(result, "tracked")
        mock_get_profile.assert_not_called()
        mock_search_by_isin.assert_not_called()

    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_isin")
    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.get_profile_with_identifiers")
    def test_review_market_commodity_uses_local_active_list_only_and_no_identifier_calls(
        self,
        mock_get_profile,
        mock_search_by_isin,
    ):
        ActiveCommodityListing.objects.create(
            symbol="GCUSD",
            name="Gold",
            exchange="COMEX",
            trade_month="",
            currency="USD",
        )
        asset = Asset.objects.create(asset_type=self.commodity_type, name="Gold", symbol="GCUSD")
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="GCUSD",
            status=AssetMarketData.Status.TRACKED,
        )

        result = HeldMarketAssetReviewService.review_asset(asset=asset)

        self.assertEqual(result, "tracked")
        mock_get_profile.assert_not_called()
        mock_search_by_isin.assert_not_called()

    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.search_by_isin")
    @patch("apps.integrations.services.held_equity_review_service.FMP_PROVIDER.get_profile_with_identifiers")
    def test_review_market_precious_metal_uses_local_commodity_list_only_and_no_identifier_calls(
        self,
        mock_get_profile,
        mock_search_by_isin,
    ):
        ActiveCommodityListing.objects.create(
            symbol="GCUSD",
            name="Gold",
            exchange="COMEX",
            trade_month="",
            currency="USD",
        )
        asset = Asset.objects.create(
            asset_type=self.precious_metal_type,
            name="Gold",
            symbol="GCUSD",
            data={"precious_metal_profile": {"metal": "gold"}},
        )
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="GCUSD",
            status=AssetMarketData.Status.TRACKED,
        )

        result = HeldMarketAssetReviewService.review_asset(asset=asset)

        self.assertEqual(result, "tracked")
        mock_get_profile.assert_not_called()
        mock_search_by_isin.assert_not_called()


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
        ActiveCryptoListing.objects.create(
            symbol="BTCUSD",
            name="Bitcoin",
            base_symbol="BTC",
            quote_currency="USD",
        )
        ActiveCommodityListing.objects.create(
            symbol="GCUSD",
            name="Gold",
            exchange="COMEX",
            trade_month="",
            currency="USD",
        )

    def test_active_equity_search_returns_filtered_results(self):
        response = self.client.get(reverse("active-equity-list"), {"q": "app"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"symbol": "AAPL", "name": "Apple Inc."}])

    def test_active_crypto_search_returns_results(self):
        response = self.client.get(reverse("active-crypto-list"), {"q": "btc"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [{"symbol": "BTCUSD", "name": "Bitcoin", "base_symbol": "BTC", "quote_currency": "USD"}],
        )

    def test_active_precious_metals_returns_derived_rows(self):
        response = self.client.get(reverse("active-precious-metal-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "metal": "gold",
                    "name": "Gold",
                    "spot_symbol": "GCUSD",
                    "spot_name": "Gold",
                    "currency": "USD",
                }
            ],
        )
