from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Account, AccountType, Holding
from assets.models import AssetPrice, AssetType
from assets.services import CustomAssetService
from fx.models import Country, FXCurrency
from portfolios.models import Portfolio, PortfolioDenomination
from portfolios.services import PortfolioValuationService
from profiles.services import ProfileBootstrapService
from schemas.models import SchemaColumn, SchemaColumnValue
from schemas.services import SchemaBootstrapService
from subscriptions.models import Plan
from users.models import User


class PortfolioValuationTests(APITestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(slug="free", defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True})

        AssetType.objects.get_or_create(name="Equity", created_by=None)

        self.user = User.objects.create_user(
            email="portfolio-valuation@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        ProfileBootstrapService.bootstrap(user=self.user)
        self.profile = self.user.profile
        self.portfolio = Portfolio.objects.get(profile=self.profile, kind=Portfolio.Kind.PERSONAL)

        self.account_type = AccountType.objects.create(
            name="Portfolio Valuation Brokerage",
            slug="portfolio-valuation-brokerage",
            is_system=True,
        )
        self.account_type.allowed_asset_types.add(AssetType.objects.get(slug="equity"))

        self.account = Account.objects.create(
            portfolio=self.portfolio,
            name="Main Account",
            account_type=self.account_type,
        )
        self.asset = CustomAssetService.create(
            profile=self.profile,
            name="Holding Asset",
            asset_type_slug="equity",
            currency_code="USD",
        ).asset
        self.holding = Holding.objects.create(account=self.account, asset=self.asset, quantity="1")

        self.schema = SchemaBootstrapService.ensure_for_account(self.account)
        self.current_value_col, _ = SchemaColumn.objects.get_or_create(
            schema=self.schema,
            identifier="current_value",
            defaults={
                "title": "Current Value",
                "data_type": "decimal",
                "is_system": False,
                "is_editable": True,
                "is_deletable": True,
                "display_order": 900,
            },
        )
        SchemaColumnValue.objects.update_or_create(
            column=self.current_value_col,
            holding=self.holding,
            defaults={"value": "1000", "source": SchemaColumnValue.Source.SYSTEM},
        )

        self.btc_asset = CustomAssetService.create(
            profile=self.profile,
            name="Bitcoin Ref",
            asset_type_slug="equity",
            currency_code="USD",
        ).asset
        AssetPrice.objects.update_or_create(
            asset=self.btc_asset,
            defaults={"price": Decimal("50000"), "source": "test"},
        )

        self.client.force_authenticate(user=self.user)

    def test_service_computes_total_and_asset_units(self):
        PortfolioDenomination.objects.create(
            portfolio=self.portfolio,
            key="btc_test",
            label="BTC",
            kind=PortfolioDenomination.Kind.ASSET_UNITS,
            asset=self.btc_asset,
            unit_label="BTC",
            is_system=False,
            display_order=99,
        )

        payload = PortfolioValuationService.valuation_payload(portfolio=self.portfolio)
        self.assertEqual(payload["total_value"], "1000.00")

        btc_row = next(item for item in payload["denominations"] if item["key"] == "btc_test")
        self.assertEqual(btc_row["value"], "0.020000")
        self.assertTrue(btc_row["is_available"])

    def test_api_valuation_and_snapshots(self):
        valuation_res = self.client.get(
            reverse("portfolio-valuation", kwargs={"portfolio_id": self.portfolio.id})
        )
        self.assertEqual(valuation_res.status_code, status.HTTP_200_OK)
        self.assertEqual(valuation_res.json()["total_value"], "1000.00")

        denom_create = self.client.post(
            reverse("portfolio-denomination-list-create", kwargs={"portfolio_id": self.portfolio.id}),
            {
                "key": "btc_test_api",
                "label": "BTC API",
                "kind": "asset_units",
                "asset_id": str(self.btc_asset.id),
                "unit_label": "BTC",
            },
            format="json",
        )
        self.assertEqual(denom_create.status_code, status.HTTP_201_CREATED)
        denom_id = denom_create.json()["id"]

        denom_patch = self.client.patch(
            reverse("portfolio-denomination-detail", kwargs={"denomination_id": denom_id}),
            {"label": "Bitcoin API"},
            format="json",
        )
        self.assertEqual(denom_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(denom_patch.json()["label"], "Bitcoin API")

        capture_res = self.client.post(
            reverse("portfolio-valuation-snapshot-capture", kwargs={"portfolio_id": self.portfolio.id}),
            {},
            format="json",
        )
        self.assertEqual(capture_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(capture_res.json()["total_value"], "1000.00")

        list_res = self.client.get(
            reverse("portfolio-valuation-snapshot-list", kwargs={"portfolio_id": self.portfolio.id})
        )
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(list_res.json()), 1)
