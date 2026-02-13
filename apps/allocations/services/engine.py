from decimal import Decimal

from django.db import transaction

from allocations.models import AllocationGapResult
from allocations.services.run_service import AllocationRunService


class AllocationEngine:
    """
    V1 scaffold evaluator.

    This intentionally writes deterministic placeholder rows so the app is
    operational in admin while you finalize analytics/target math rules.
    """

    @staticmethod
    @transaction.atomic
    def evaluate(*, scenario, triggered_by=None, as_of=None):
        run = AllocationRunService.create_pending(
            scenario=scenario,
            triggered_by=triggered_by,
            as_of=as_of,
        )

        AllocationRunService.mark_running(run=run)

        try:
            rows = []

            for dimension in scenario.dimensions.filter(is_active=True):
                for target in dimension.targets.filter(is_active=True):
                    target_percent = target.target_percent or Decimal("0")
                    target_value = target.target_value or Decimal("0")

                    rows.append(
                        AllocationGapResult(
                            run=run,
                            dimension=dimension,
                            target=target,
                            bucket_label_snapshot=target.label,
                            actual_value=Decimal("0"),
                            target_value=target_value,
                            gap_value=target_value,
                            actual_percent=Decimal("0"),
                            target_percent=target_percent,
                            gap_percent=target_percent,
                            holding_count=0,
                        )
                    )

            if rows:
                AllocationGapResult.objects.bulk_create(rows)

            AllocationRunService.mark_success(run=run)
            return run

        except Exception as exc:
            AllocationRunService.mark_failed(run=run, error=exc)
            raise
