from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Account, AccountType, Holding
from assets.models import AssetType
from assets.services import CustomAssetService
from analytics.models import (
    Analytic,
    AnalyticDimension,
    AssetDimensionExposure,
    DimensionBucket,
)
from analytics.seeders import seed_starter_templates_for_portfolio
from analytics.services import AnalyticsEngine
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from schemas.models import SchemaColumn, SchemaColumnValue
from schemas.services.bootstrap import SchemaBootstrapService
from subscriptions.models import Plan
from users.models import User


class AnalyticsEngineTests(TestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(slug="free", defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True})
        AssetType.objects.get_or_create(name="Equity", created_by=None)

        self.user = User.objects.create_user(
            email="analytics-engine@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        ProfileBootstrapService.bootstrap(user=self.user)
        self.profile = self.user.profile
        self.portfolio = Portfolio.objects.get(profile=self.profile, kind=Portfolio.Kind.PERSONAL)

        self.account_type = AccountType.objects.create(name="Analytics Brokerage", slug="analytics-brokerage", is_system=True)
        self.account_type.allowed_asset_types.add(AssetType.objects.get(slug="equity"))

        self.account = Account.objects.create(
            portfolio=self.portfolio,
            name="Main Account",
            account_type=self.account_type,
        )

        self.asset_a = CustomAssetService.create(
            profile=self.profile,
            name="Coal Corp",
            asset_type_slug="equity",
            currency_code="USD",
        ).asset
        self.asset_b = CustomAssetService.create(
            profile=self.profile,
            name="Green Corp",
            asset_type_slug="equity",
            currency_code="USD",
        ).asset

        self.holding_a = Holding.objects.create(account=self.account, asset=self.asset_a, quantity="10")
        self.holding_b = Holding.objects.create(account=self.account, asset=self.asset_b, quantity="20")

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

        self.sector_col = SchemaColumn.objects.create(
            schema=self.schema,
            identifier="sector",
            title="Sector",
            data_type="string",
            is_system=False,
            is_editable=True,
            is_deletable=True,
            display_order=999,
        )

        SchemaColumnValue.objects.update_or_create(
            column=self.current_value_col,
            holding=self.holding_a,
            defaults={"value": "100", "source": SchemaColumnValue.Source.SYSTEM},
        )
        SchemaColumnValue.objects.update_or_create(
            column=self.current_value_col,
            holding=self.holding_b,
            defaults={"value": "300", "source": SchemaColumnValue.Source.SYSTEM},
        )

        SchemaColumnValue.objects.update_or_create(
            column=self.sector_col,
            holding=self.holding_a,
            defaults={"value": "Coal", "source": SchemaColumnValue.Source.USER},
        )
        SchemaColumnValue.objects.update_or_create(
            column=self.sector_col,
            holding=self.holding_b,
            defaults={"value": "Green Energy", "source": SchemaColumnValue.Source.USER},
        )

    def test_compute_categorical_and_weighted_dimensions(self):
        analytic = Analytic.objects.create(
            portfolio=self.portfolio,
            name="allocation",
            label="Allocation",
            value_identifier="current_value",
        )

        categorical = AnalyticDimension.objects.create(
            analytic=analytic,
            name="sector",
            label="Sector",
            dimension_type=AnalyticDimension.DimensionType.CATEGORICAL,
            source_type=AnalyticDimension.SourceType.SCV_IDENTIFIER,
            source_identifier="sector",
            display_order=1,
        )
        DimensionBucket.objects.create(dimension=categorical, key="unknown", label="Unknown", is_unknown_bucket=True)

        weighted = AnalyticDimension.objects.create(
            analytic=analytic,
            name="energy_mix",
            label="Energy Mix",
            dimension_type=AnalyticDimension.DimensionType.WEIGHTED,
            source_type=AnalyticDimension.SourceType.ASSET_EXPOSURE,
            display_order=2,
        )

        coal = DimensionBucket.objects.create(dimension=weighted, key="coal", label="Coal")
        green = DimensionBucket.objects.create(dimension=weighted, key="green", label="Green")
        DimensionBucket.objects.create(dimension=weighted, key="unknown", label="Unknown", is_unknown_bucket=True)

        AssetDimensionExposure.objects.create(dimension=weighted, asset=self.asset_a, bucket=coal, weight="0.7")
        AssetDimensionExposure.objects.create(dimension=weighted, asset=self.asset_a, bucket=green, weight="0.3")
        AssetDimensionExposure.objects.create(dimension=weighted, asset=self.asset_b, bucket=green, weight="1")

        run = AnalyticsEngine.compute(analytic=analytic, triggered_by=self.user)
        self.assertEqual(run.status, "success")

        weighted_results = {r.bucket_label_snapshot: r for r in run.results.filter(dimension=weighted)}
        self.assertEqual(weighted_results["Coal"].total_value, Decimal("70.00"))
        self.assertEqual(weighted_results["Green"].total_value, Decimal("330.00"))

        categorical_results = {r.bucket_label_snapshot: r for r in run.results.filter(dimension=categorical)}
        self.assertEqual(categorical_results["Coal"].total_value, Decimal("100.00"))
        self.assertEqual(categorical_results["Green Energy"].total_value, Decimal("300.00"))


class AnalyticsAPITests(APITestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(slug="free", defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True})

        self.user = User.objects.create_user(
            email="analytics-api@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        self.other_user = User.objects.create_user(
            email="analytics-other@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )

        ProfileBootstrapService.bootstrap(user=self.user)
        ProfileBootstrapService.bootstrap(user=self.other_user)

        self.portfolio = Portfolio.objects.get(profile=self.user.profile, kind=Portfolio.Kind.PERSONAL)
        self.other_portfolio = Portfolio.objects.get(profile=self.other_user.profile, kind=Portfolio.Kind.PERSONAL)

        self.client.force_authenticate(user=self.user)

    def test_create_run_and_get_latest_results(self):
        create_response = self.client.post(
            reverse("analytics-list-create"),
            {
                "portfolio_id": self.portfolio.id,
                "name": "overview",
                "label": "Overview",
                "value_identifier": "current_value",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        analytic_id = create_response.json()["id"]

        dim_response = self.client.post(
            reverse("analytics-dimension-list-create", kwargs={"analytic_id": analytic_id}),
            {
                "name": "sector",
                "label": "Sector",
                "dimension_type": "categorical",
                "source_type": "scv_identifier",
                "source_identifier": "sector",
            },
            format="json",
        )
        self.assertEqual(dim_response.status_code, status.HTTP_201_CREATED)

        run_response = self.client.post(
            reverse("analytics-run", kwargs={"analytic_id": analytic_id}),
            {},
            format="json",
        )
        self.assertEqual(run_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(run_response.json()["status"], "success")

        latest = self.client.get(reverse("analytics-results-latest", kwargs={"analytic_id": analytic_id}))
        self.assertEqual(latest.status_code, status.HTTP_200_OK)
        self.assertEqual(latest.json()["analytic_id"], analytic_id)

    def test_cannot_access_other_users_analytic(self):
        analytic = Analytic.objects.create(
            portfolio=self.other_portfolio,
            name="private",
            label="Private",
            value_identifier="current_value",
        )
        response = self.client.get(reverse("analytics-detail", kwargs={"analytic_id": analytic.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnalyticsStarterSeederTests(TestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(slug="free", defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True})

        self.user = User.objects.create_user(
            email="analytics-seed@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        ProfileBootstrapService.bootstrap(user=self.user)
        self.portfolio = Portfolio.objects.get(profile=self.user.profile, kind=Portfolio.Kind.PERSONAL)

    def test_seed_starters_is_idempotent(self):
        first = seed_starter_templates_for_portfolio(portfolio_id=self.portfolio.id)
        second = seed_starter_templates_for_portfolio(portfolio_id=self.portfolio.id)

        self.assertGreater(first["analytics_created"], 0)
        self.assertGreater(first["dimensions_created"], 0)
        self.assertGreater(first["buckets_created"], 0)

        self.assertEqual(second["analytics_created"], 0)
        self.assertEqual(second["dimensions_created"], 0)
        self.assertEqual(second["buckets_created"], 0)

        self.assertTrue(
            Analytic.objects.filter(
                portfolio=self.portfolio,
                name="allocation_overview",
            ).exists()
        )
        self.assertTrue(
            AnalyticDimension.objects.filter(
                analytic__portfolio=self.portfolio,
                name="energy_mix",
            ).exists()
        )
        self.assertTrue(
            DimensionBucket.objects.filter(
                dimension__analytic__portfolio=self.portfolio,
                key="coal_thermal",
            ).exists()
        )
