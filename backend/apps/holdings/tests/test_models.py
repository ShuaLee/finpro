from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.assets.models import Asset, AssetType
from apps.holdings.models import Container, Holding, Portfolio


class HoldingsModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="holdings@example.com",
            password="StrongPass123!",
        )
        self.profile = self.user.profile
        self.portfolio = Portfolio.objects.create(
            profile=self.profile,
            name="Main Portfolio",
            is_default=True,
        )
        self.container = Container.objects.create(
            portfolio=self.portfolio,
            name="Main Collection",
        )
        self.asset_type = AssetType.objects.create(name="Equity")
        self.asset = Asset.objects.create(
            asset_type=self.asset_type,
            name="Apple Inc.",
            symbol="AAPL",
        )

    def test_portfolio_owner_cannot_change(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
        )
        self.portfolio.profile = other_user.profile

        with self.assertRaises(ValidationError):
            self.portfolio.full_clean()

    def test_container_portfolio_cannot_change(self):
        other_portfolio = Portfolio.objects.create(
            profile=self.profile,
            name="Other Portfolio",
        )
        self.container.portfolio = other_portfolio

        with self.assertRaises(ValidationError):
            self.container.full_clean()

    def test_holding_computed_values_are_derived_from_quantity_and_unit_fields(self):
        holding = Holding.objects.create(
            container=self.container,
            asset=self.asset,
            quantity=Decimal("10"),
            unit_value=Decimal("215.50"),
            unit_cost_basis=Decimal("180.25"),
        )

        self.assertEqual(holding.current_value, Decimal("2155.00"))
        self.assertEqual(holding.invested_value, Decimal("1802.50"))

    def test_holding_quantity_must_be_positive(self):
        holding = Holding(
            container=self.container,
            asset=self.asset,
            quantity=Decimal("0"),
        )

        with self.assertRaises(ValidationError):
            holding.full_clean()

    def test_holding_container_and_asset_are_immutable(self):
        holding = Holding.objects.create(
            container=self.container,
            asset=self.asset,
            quantity=Decimal("1"),
        )
        other_container = Container.objects.create(
            portfolio=self.portfolio,
            name="Other Collection",
        )
        other_asset = Asset.objects.create(
            asset_type=self.asset_type,
            name="Tesla Inc.",
            symbol="TSLA",
        )

        holding.container = other_container
        with self.assertRaises(ValidationError):
            holding.full_clean()

        holding.refresh_from_db()
        holding.asset = other_asset
        with self.assertRaises(ValidationError):
            holding.full_clean()

    def test_holding_is_unique_per_container_and_asset(self):
        Holding.objects.create(
            container=self.container,
            asset=self.asset,
            quantity=Decimal("1"),
        )

        duplicate = Holding(
            container=self.container,
            asset=self.asset,
            quantity=Decimal("2"),
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()
