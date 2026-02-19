from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from django.utils.text import slugify

from analytics.models import AnalyticDimension, AnalyticResult


@dataclass
class BucketActual:
    key: str
    label: str
    actual_value: object
    holding_count: int


class AllocationActualsResolver:
    @staticmethod
    def _resolve_dimension(*, portfolio, source_identifier, source_analytic_name=None):
        qs = AnalyticDimension.objects.filter(
            analytic__portfolio=portfolio,
            name=source_identifier,
        )
        if source_analytic_name:
            qs = qs.filter(analytic__name=source_analytic_name)

        return qs.order_by("analytic_id").first()

    @staticmethod
    def _latest_successful_results_for_dimension(*, analytic_dimension):
        if not analytic_dimension:
            return []

        latest_run = (
            analytic_dimension.analytic.runs.filter(status="success")
            .only("id")
            .first()
        )
        if not latest_run:
            return []

        return list(
            AnalyticResult.objects.filter(run=latest_run, dimension=analytic_dimension)
            .select_related("bucket")
            .order_by("-total_value")
        )

    @staticmethod
    def actuals_by_bucket(*, portfolio, source_identifier, source_analytic_name=None):
        dimension = AllocationActualsResolver._resolve_dimension(
            portfolio=portfolio,
            source_identifier=source_identifier,
            source_analytic_name=source_analytic_name,
        )
        results = AllocationActualsResolver._latest_successful_results_for_dimension(
            analytic_dimension=dimension
        )

        actuals = {}
        for result in results:
            key = result.bucket.key if result.bucket_id else slugify(result.bucket_label_snapshot)
            if not key:
                key = "unknown"
            actuals[key] = BucketActual(
                key=key,
                label=result.bucket_label_snapshot,
                actual_value=result.total_value,
                holding_count=result.holding_count,
            )

        return actuals

    @staticmethod
    def sum_actual_values(*, actuals_by_bucket):
        total = 0
        for item in actuals_by_bucket.values():
            total += item.actual_value
        return total
