from django.db import transaction

from accounts.models import Holding
from analytics.models import Analytic
from analytics.services.aggregation_service import AggregationService
from analytics.services.result_writer import ResultWriterService
from analytics.services.run_service import AnalyticRunService


class AnalyticsEngine:
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

            dimension_rows = []

            for dimension in analytic.dimensions.filter(is_active=True):
                rows = AggregationService.aggregate_dimension(
                    analytic=analytic,
                    dimension=dimension,
                    holdings=holdings,
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
