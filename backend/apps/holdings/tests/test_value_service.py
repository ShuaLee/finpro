from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.assets.models import Asset, AssetPrice, AssetType
from apps.holdings.models import Container, Holding, HoldingOverride, Portfolio
from apps.holdings.services import HoldingValueService


class HoldingValueServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="holding-values@example.com",
            password="StrongPass123!",
        )
        self.profile = self.user.profile
        self.portfolio = Portfolio.objects.create(profile=self.profile, name="Main")
        self.container = Container.objects.create(portfolio=self.portfolio, name="Brokerage")
        self.asset_type = AssetType.objects.create(name="Equity")
        self.asset = Asset.objects.create(
            asset_type=self.asset_type,
            name="Apple Inc.",
            symbol="AAPL",
            data={
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "country": "US",
                "exchange": "NASDAQ",
                "currency": "USD",
            },
        )
        AssetPrice.objects.create(asset=self.asset, price=Decimal("200"))
        self.holding = Holding.objects.create(
            container=self.container,
            asset=self.asset,
            quantity=Decimal("3"),
            unit_value=Decimal("198"),
            unit_cost_basis=Decimal("150"),
        )

    def test_effective_price_uses_holding_unit_value_before_asset_price(self):
        self.assertEqual(
            HoldingValueService.get_effective_value(holding=self.holding, key="price"),
            Decimal("198"),
        )
        self.assertEqual(
            HoldingValueService.get_effective_value(holding=self.holding, key="current_value"),
            Decimal("594"),
        )

    def test_override_beats_asset_metadata_and_custom_fact_values_are_resolved(self):
        definition = HoldingValueService.create_fact_definition(
            portfolio=self.portfolio,
            key="conviction_score",
            label="Conviction Score",
            data_type="decimal",
        )
        HoldingValueService.upsert_fact_value(
            holding=self.holding,
            definition=definition,
            value="0.85",
        )
        HoldingValueService.upsert_override(
            holding=self.holding,
            key="sector",
            data_type="string",
            value="AI Infrastructure",
        )

        self.assertEqual(
            HoldingValueService.get_effective_value(holding=self.holding, key="sector"),
            "AI Infrastructure",
        )
        self.assertEqual(
            HoldingValueService.get_effective_value(holding=self.holding, key="conviction_score"),
            Decimal("0.85"),
        )
        self.assertTrue(HoldingOverride.objects.filter(holding=self.holding, key="sector").exists())
