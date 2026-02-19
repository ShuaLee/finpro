from collections import defaultdict

from django.db import transaction

from accounts.models import Holding
from analytics.models import (
    Analytic,
    AssetDimensionExposure,
    HoldingDimensionExposureOverride,
)
from analytics.services.aggregation_service import AggregationService
from analytics.services.results_writer import ResultWriterService
from analytics.services.run_service import AnalyticRunService
from schemas.models import SchemaColumnValue


class AnalyticsEngine:
    @staticmethod
    def _values_for_holdings(*, holdings, identifiers):
        values_by_holding = defaultdict(dict)
        if not holdings or not identifiers:
            return values_by_holding

        rows = (
            SchemaColumnValue.objects.filter(
                holding_id__in=[h.id for h in holdings],
                column__identifier__in=identifiers,
            )
            .select_related("column")
            .only("holding_id", "value", "column__identifier")
        )
        for row in rows:
            values_by_holding[row.holding_id][row.column.identifier] = row.value

        return values_by_holding

    @staticmethod
    def _exposure_maps_for_dimension(*, dimension, holdings):
        asset_exposures_by_asset = defaultdict(list)
        holding_overrides_by_holding = defaultdict(list)

        asset_ids = [h.asset_id for h in holdings if h.asset_id]
        holding_ids = [h.id for h in holdings]

        if asset_ids:
            exposures = (
                AssetDimensionExposure.objects.filter(
                    dimension=dimension,
                    asset_id__in=asset_ids,
                    bucket__is_active=True,
                )
                .select_related("bucket")
                .order_by("bucket__display_order", "bucket__label")
            )
            for exposure in exposures:
                asset_exposures_by_asset[exposure.asset_id].append(exposure)

        if holding_ids:
            overrides = (
                HoldingDimensionExposureOverride.objects.filter(
                    dimension=dimension,
                    holding_id__in=holding_ids,
                    bucket__is_active=True,
                )
                .select_related("bucket")
                .order_by("bucket__display_order", "bucket__label")
            )
            for override in overrides:
                holding_overrides_by_holding[override.holding_id].append(override)

        return asset_exposures_by_asset, holding_overrides_by_holding

    @staticmethod
    @transaction.atomic
    def compute(*, analytic: Analytic, triggered_by=None, as_of=None):
        run = AnalyticRunService.create_pending(
            analytic=analytic,
            triggered_by=triggered_by,
            as_of=as_of,
        )
        AnalyticRunService.mark_running(run=run)

        try:
            holdings = list(
                Holding.objects.filter(
                    account__portfolio=analytic.portfolio,
                ).select_related("account", "asset")
            )

            dimensions = list(analytic.dimensions.filter(is_active=True).prefetch_related("buckets"))

            identifiers = {analytic.value_identifier}
            for dimension in dimensions:
                if dimension.dimension_type == dimension.DimensionType.CATEGORICAL and dimension.source_identifier:
                    identifiers.add(dimension.source_identifier)

            values_by_holding = AnalyticsEngine._values_for_holdings(
                holdings=holdings,
                identifiers=identifiers,
            )

            dimension_rows = []
            for dimension in dimensions:
                asset_map, holding_map = AnalyticsEngine._exposure_maps_for_dimension(
                    dimension=dimension,
                    holdings=holdings,
                )

                rows = AggregationService.aggregate_dimension(
                    analytic=analytic,
                    dimension=dimension,
                    holdings=holdings,
                    values_by_holding=values_by_holding,
                    asset_exposures_by_asset=asset_map,
                    override_exposures_by_holding=holding_map,
                )
                dimension_rows.append((dimension, rows))

            ResultWriterService.replace_results_for_run(
                run=run,
                dimension_rows=dimension_rows,
            )

            AnalyticRunService.mark_success(run=run)
            return run
        except Exception as exc:
            AnalyticRunService.mark_failed(run=run, error=exc)
            raise
