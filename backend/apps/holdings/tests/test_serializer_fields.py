from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from unittest.mock import patch

from apps.assets.models import Asset, AssetMarketData, AssetPrice, AssetType
from apps.holdings.models import Container, Holding, Portfolio
from apps.holdings.serializers import HoldingSerializer


@override_settings(ASSET_PRICE_CACHE_TTL_SECONDS=600)
class HoldingSerializerFieldTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="holding-serializer@example.com",
            password="StrongPass123!",
        )
        self.portfolio = Portfolio.objects.create(profile=self.user.profile, name="Main")
        self.container = Container.objects.create(portfolio=self.portfolio, name="Brokerage")
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
            price=Decimal("210.15"),
            change=Decimal("1.25"),
            volume=100,
            source="FMP",
        )
        self.holding = Holding.objects.create(
            container=self.container,
            asset=self.asset,
            quantity=Decimal("2"),
        )

    def test_serializer_exposes_asset_price_fields(self):
        data = HoldingSerializer(self.holding).data

        self.assertEqual(data["asset_current_price"], "210.150000000000000000")
        self.assertTrue(data["asset_current_price_is_fresh"])
        self.assertIsNotNone(data["asset_current_price_as_of"])

    @patch("apps.holdings.services.holding_formula_service.FXRateService.get_rate")
    def test_serializer_exposes_formula_fields(self, mock_get_rate):
        mock_get_rate.return_value = Decimal("1")
        self.asset.data = {"currency": "USD"}
        self.asset.save(update_fields=["data"])
        self.user.profile.currency = "USD"
        self.user.profile.save(update_fields=["currency"])

        data = HoldingSerializer(self.holding).data

        self.assertEqual(data["fx_rate"], "1.0000000000")
        self.assertEqual(data["market_value"], "420.300000000000000000")
        self.assertEqual(data["current_value_profile"], "420.300000000000000000")

    def test_serializer_marks_asset_price_stale_when_ttl_passed(self):
        AssetPrice.objects.filter(asset=self.asset).update(
            as_of=timezone.now() - timedelta(minutes=11)
        )
        self.holding.refresh_from_db()

        data = HoldingSerializer(self.holding).data

        self.assertFalse(data["asset_current_price_is_fresh"])
