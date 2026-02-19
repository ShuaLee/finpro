from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Account, AccountType, Holding
from allocations.models import AllocationDimension, AllocationPlan, AllocationScenario, AllocationTarget
from allocations.services.engine import AllocationEngine
from assets.models import AssetType
from assets.services import CustomAssetService
from analytics.models import Analytic, AnalyticDimension, AnalyticResult, AnalyticRun, DimensionBucket
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from schemas.models import SchemaColumn, SchemaColumnValue
from schemas.services.bootstrap import SchemaBootstrapService
from subscriptions.models import Plan
from users.models import User


class AllocationEngineTests(TestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(slug="free", defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True})
        AssetType.objects.get_or_create(name="Equity", created_by=None)

        self.user = User.objects.create_user(
            email="allocation-engine@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        ProfileBootstrapService.bootstrap(user=self.user)
        self.profile = self.user.profile
        self.portfolio = Portfolio.objects.get(profile=self.profile, kind=Portfolio.Kind.PERSONAL)

        self.account_type = AccountType.objects.create(name="Alloc Brokerage", slug="alloc-brokerage", is_system=True)
        self.account_type.allowed_asset_types.add(AssetType.objects.get(slug="equity"))

        self.account = Account.objects.create(
            portfolio=self.portfolio,
            name="Main Account",
            account_type=self.account_type,
        )

        asset_a = CustomAssetService.create(
            profile=self.profile,
            name="Met Coal Asset",
            asset_type_slug="equity",
            currency_code="USD",
        ).asset
        asset_b = CustomAssetService.create(
            profile=self.profile,
            name="Thermal Coal Asset",
            asset_type_slug="equity",
            currency_code="USD",
        ).asset

        holding_a = Holding.objects.create(account=self.account, asset=asset_a, quantity="1")
        holding_b = Holding.objects.create(account=self.account, asset=asset_b, quantity="1")

        schema = SchemaBootstrapService.ensure_for_account(self.account)
        current_value_col, _ = SchemaColumn.objects.get_or_create(
            schema=schema,
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
            column=current_value_col,
            holding=holding_a,
            defaults={"value": "100", "source": SchemaColumnValue.Source.SYSTEM},
        )
        SchemaColumnValue.objects.update_or_create(
            column=current_value_col,
            holding=holding_b,
            defaults={"value": "300", "source": SchemaColumnValue.Source.SYSTEM},
        )

        analytic = Analytic.objects.create(
            portfolio=self.portfolio,
            name="energy_exposure",
            label="Energy Exposure",
            value_identifier="current_value",
        )
        analytic_dimension = AnalyticDimension.objects.create(
            analytic=analytic,
            name="energy_mix",
            label="Energy Mix",
            dimension_type=AnalyticDimension.DimensionType.WEIGHTED,
            source_type=AnalyticDimension.SourceType.ASSET_EXPOSURE,
        )
        met_coal = DimensionBucket.objects.create(dimension=analytic_dimension, key="met_coal", label="Met Coal")
        thermal = DimensionBucket.objects.create(dimension=analytic_dimension, key="thermal_coal", label="Thermal Coal")

        run = AnalyticRun.objects.create(
            analytic=analytic,
            status=AnalyticRun.Status.SUCCESS,
            started_at=timezone.now(),
            finished_at=timezone.now(),
        )
        AnalyticResult.objects.create(
            run=run,
            dimension=analytic_dimension,
            bucket=met_coal,
            bucket_label_snapshot="Met Coal",
            total_value=Decimal("100.00"),
            percentage=Decimal("0.25"),
            holding_count=1,
        )
        AnalyticResult.objects.create(
            run=run,
            dimension=analytic_dimension,
            bucket=thermal,
            bucket_label_snapshot="Thermal Coal",
            total_value=Decimal("300.00"),
            percentage=Decimal("0.75"),
            holding_count=1,
        )

        self.plan = AllocationPlan.objects.create(
            portfolio=self.portfolio,
            name="base_plan",
            label="Base Plan",
            base_value_identifier="current_value",
        )
        self.scenario = AllocationScenario.objects.create(
            plan=self.plan,
            name="base",
            label="Base",
            is_default=True,
        )
        self.dimension = AllocationDimension.objects.create(
            scenario=self.scenario,
            name="energy_alloc",
            label="Energy Allocation",
            source_identifier="energy_mix",
            source_analytic_name="energy_exposure",
            denominator_mode=AllocationDimension.DenominatorMode.BASE_SCOPE_TOTAL,
        )
        AllocationTarget.objects.create(
            dimension=self.dimension,
            key="met_coal",
            label="Met Coal",
            target_percent=Decimal("0.30"),
        )
        AllocationTarget.objects.create(
            dimension=self.dimension,
            key="thermal_coal",
            label="Thermal Coal",
            target_percent=Decimal("0.70"),
        )

    def test_engine_evaluates_against_latest_analytics(self):
        run = AllocationEngine.evaluate(scenario=self.scenario, triggered_by=self.user)
        self.assertEqual(run.status, "success")

        rows = {r.bucket_key_snapshot: r for r in run.results.filter(dimension=self.dimension)}
        self.assertEqual(rows["met_coal"].actual_value, Decimal("100.00"))
        self.assertEqual(rows["met_coal"].target_value, Decimal("120.00"))
        self.assertEqual(rows["met_coal"].gap_value, Decimal("20.00"))

        self.assertEqual(rows["thermal_coal"].actual_value, Decimal("300.00"))
        self.assertEqual(rows["thermal_coal"].target_value, Decimal("280.00"))
        self.assertEqual(rows["thermal_coal"].gap_value, Decimal("-20.00"))


class AllocationAPITests(APITestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(slug="free", defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True})

        self.user = User.objects.create_user(
            email="allocation-api@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        self.other_user = User.objects.create_user(
            email="allocation-other@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )

        ProfileBootstrapService.bootstrap(user=self.user)
        ProfileBootstrapService.bootstrap(user=self.other_user)

        self.portfolio = Portfolio.objects.get(profile=self.user.profile, kind=Portfolio.Kind.PERSONAL)
        self.other_portfolio = Portfolio.objects.get(profile=self.other_user.profile, kind=Portfolio.Kind.PERSONAL)

        self.client.force_authenticate(user=self.user)

    def test_create_plan_scenario_dimension_target(self):
        plan_res = self.client.post(
            reverse("allocation-plan-list-create"),
            {
                "portfolio_id": self.portfolio.id,
                "name": "goal_plan",
                "label": "Goal Plan",
                "base_value_identifier": "current_value",
            },
            format="json",
        )
        self.assertEqual(plan_res.status_code, status.HTTP_201_CREATED)
        plan_id = plan_res.json()["id"]

        scenario_res = self.client.post(
            reverse("allocation-scenario-list-create", kwargs={"plan_id": plan_id}),
            {
                "name": "base",
                "label": "Base",
                "is_default": True,
            },
            format="json",
        )
        self.assertEqual(scenario_res.status_code, status.HTTP_201_CREATED)
        scenario_id = scenario_res.json()["id"]

        dimension_res = self.client.post(
            reverse("allocation-dimension-list-create", kwargs={"scenario_id": scenario_id}),
            {
                "name": "energy_alloc",
                "label": "Energy Allocation",
                "source_identifier": "energy_mix",
                "source_analytic_name": "energy_exposure",
                "denominator_mode": "base_scope_total",
            },
            format="json",
        )
        self.assertEqual(dimension_res.status_code, status.HTTP_201_CREATED)
        dimension_id = dimension_res.json()["id"]

        target_res = self.client.post(
            reverse("allocation-target-list-create", kwargs={"dimension_id": dimension_id}),
            {
                "key": "met_coal",
                "label": "Met Coal",
                "target_percent": "0.25",
            },
            format="json",
        )
        self.assertEqual(target_res.status_code, status.HTTP_201_CREATED)

    def test_cannot_access_other_users_plan(self):
        foreign_plan = AllocationPlan.objects.create(
            portfolio=self.other_portfolio,
            name="private_plan",
            label="Private Plan",
        )
        response = self.client.get(reverse("allocation-plan-detail", kwargs={"plan_id": foreign_plan.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
