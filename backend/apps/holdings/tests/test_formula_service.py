from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.assets.models import Asset, AssetPrice, AssetType
from apps.holdings.models import Container, Holding, Portfolio
from apps.holdings.services import HoldingFormulaService


class HoldingFormulaServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="holding-formulas@example.com",
            password="StrongPass123!",
        )
        self.user.profile.currency = "CAD"
        self.user.profile.save(update_fields=["currency"])
        self.portfolio = Portfolio.objects.create(profile=self.user.profile, name="Main")
        self.container = Container.objects.create(portfolio=self.portfolio, name="Brokerage")
        self.asset_type = AssetType.objects.create(name="Equity")
        self.asset = Asset.objects.create(
            asset_type=self.asset_type,
            name="Apple Inc.",
            symbol="AAPL",
            data={"currency": "USD"},
        )
        AssetPrice.objects.create(asset=self.asset, price=Decimal("210"))
        self.holding = Holding.objects.create(
            container=self.container,
            asset=self.asset,
            quantity=Decimal("2"),
            unit_cost_basis=Decimal("150"),
        )

    @patch("apps.holdings.services.holding_formula_service.FXRateService.get_rate")
    def test_formula_summary_uses_fx_rate_for_profile_currency_outputs(self, mock_get_rate):
        mock_get_rate.return_value = Decimal("1.35")

        self.assertEqual(
            HoldingFormulaService.evaluate(holding=self.holding, identifier="market_value"),
            Decimal("420"),
        )
        self.assertEqual(
            HoldingFormulaService.evaluate(holding=self.holding, identifier="current_value"),
            Decimal("567.00"),
        )
        self.assertEqual(
            HoldingFormulaService.evaluate(holding=self.holding, identifier="cost_basis"),
            Decimal("405.00"),
        )
        self.assertEqual(
            HoldingFormulaService.evaluate(holding=self.holding, identifier="unrealized_gain"),
            Decimal("162.00"),
        )
        self.assertEqual(
            HoldingFormulaService.evaluate(holding=self.holding, identifier="unrealized_gain_pct"),
            Decimal("0.4"),
        )
