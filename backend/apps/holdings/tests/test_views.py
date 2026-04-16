from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.assets.models import Asset, AssetMarketData, AssetType
from apps.holdings.models import Container, Holding, Portfolio
from apps.integrations.models import ActiveCommodityListing, ActiveCryptoListing, ActiveEquityListing


class DashboardLayoutStateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="dashboard-layout@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(self.user)

    def test_get_empty_dashboard_layout_state(self):
        response = self.client.get(reverse("dashboard-layout-state"), {"scope": "dashboards"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scope"], "dashboards")
        self.assertEqual(response.data["active_layout_id"], "")
        self.assertEqual(response.data["layouts"], [])

    def test_put_then_get_dashboard_layout_state(self):
        payload = {
            "scope": "dashboards",
            "active_layout_id": "layout_main",
            "layouts": [
                {
                    "id": "layout_main",
                    "name": "Main",
                    "viewportLayouts": {
                        "desktop": {"tiles": [{"id": 1, "slot": 2, "colSpan": 3, "rowSpan": 2}]},
                    },
                },
            ],
        }

        put_response = self.client.put(reverse("dashboard-layout-state"), payload, format="json")
        get_response = self.client.get(reverse("dashboard-layout-state"), {"scope": "dashboards"})

        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data["active_layout_id"], "layout_main")
        self.assertEqual(get_response.data["layouts"], payload["layouts"])

    def test_dashboard_layout_state_is_user_scoped(self):
        payload = {
            "scope": "dashboards",
            "active_layout_id": "layout_main",
            "layouts": [{"id": "layout_main", "name": "Main"}],
        }
        self.client.put(reverse("dashboard-layout-state"), payload, format="json")

        other_user = get_user_model().objects.create_user(
            email="other-dashboard-layout@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(other_user)
        response = self.client.get(reverse("dashboard-layout-state"), {"scope": "dashboards"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_layout_id"], "")
        self.assertEqual(response.data["layouts"], [])


class HoldingCreateWithActiveEquityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="holding-flow@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(self.user)
        self.portfolio = Portfolio.objects.create(
            profile=self.user.profile,
            name="Main Portfolio",
        )
        self.container = Container.objects.create(
            portfolio=self.portfolio,
            name="Brokerage",
        )
        AssetType.objects.create(name="Equity")
        AssetType.objects.create(name="Cryptocurrency")
        AssetType.objects.create(name="Commodity")
        AssetType.objects.create(name="Precious Metal")
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

    @patch("apps.holdings.views.ActiveEquityAssetService.ensure_identity_for_held_asset")
    def test_create_with_active_equity_symbol_promotes_asset_and_creates_holding(self, mock_ensure_identity):
        response = self.client.post(
            reverse("holding-create-with-asset"),
            {
                "container": self.container.pk,
                "active_equity_symbol": "aapl",
                "quantity": "3",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        holding = Holding.objects.get(container=self.container)
        self.assertEqual(holding.asset.symbol, "AAPL")
        self.assertIsNone(holding.asset.owner)
        self.assertEqual(holding.asset.market_data.provider_symbol, "AAPL")
        mock_ensure_identity.assert_called_once()

    def test_create_with_active_crypto_symbol_promotes_crypto_asset(self):
        response = self.client.post(
            reverse("holding-create-with-asset"),
            {
                "container": self.container.pk,
                "active_crypto_symbol": "BTCUSD",
                "quantity": "1.5",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        holding = Holding.objects.get(container=self.container)
        self.assertIn(holding.asset.asset_type.slug, {"crypto", "cryptocurrency"})
        self.assertEqual(holding.asset.symbol, "BTCUSD")

    def test_create_with_precious_metal_code_promotes_precious_metal_asset(self):
        response = self.client.post(
            reverse("holding-create-with-asset"),
            {
                "container": self.container.pk,
                "precious_metal_code": "gold",
                "quantity": "2",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        holding = Holding.objects.get(container=self.container)
        self.assertEqual(holding.asset.asset_type.slug, "precious_metal")
        self.assertEqual(holding.asset.symbol, "GCUSD")

    @patch("apps.holdings.views.ActiveEquityAssetService.ensure_identity_for_held_asset")
    def test_create_with_existing_public_equity_also_runs_identity_enrichment(self, mock_ensure_identity):
        equity_type = AssetType.objects.get(slug="equity")
        asset = Asset.objects.create(
            asset_type=equity_type,
            name="Apple Inc.",
            symbol="AAPL",
        )
        AssetMarketData.objects.create(
            asset=asset,
            provider=AssetMarketData.Provider.FMP,
            provider_symbol="AAPL",
            status=AssetMarketData.Status.TRACKED,
        )

        response = self.client.post(
            reverse("holding-list-create"),
            {
                "container": self.container.pk,
                "asset": str(asset.pk),
                "quantity": "2",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        mock_ensure_identity.assert_called_once_with(asset=asset)
