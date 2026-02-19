from decimal import Decimal

from django.db import transaction

from allocations.models import AllocationGapResult
from allocations.services.actuals_resolver import AllocationActualsResolver
from allocations.services.base_value_service import AllocationBaseValueService
from allocations.services.run_service import AllocationRunService


class AllocationEngine:
    @staticmethod
    def _safe_percent(*, value, denominator):
        if not denominator or denominator <= 0:
            return Decimal("0")
        return Decimal(str(value)) / Decimal(str(denominator))

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
            plan = scenario.plan
            base_total = AllocationBaseValueService.base_total_for_plan(plan=plan)

            rows = []
            for dimension in scenario.dimensions.filter(is_active=True).prefetch_related("targets"):
                actual_map = AllocationActualsResolver.actuals_by_bucket(
                    portfolio=plan.portfolio,
                    source_identifier=dimension.source_identifier,
                    source_analytic_name=dimension.source_analytic_name,
                )
                actual_total = AllocationActualsResolver.sum_actual_values(actuals_by_bucket=actual_map)

                if dimension.denominator_mode == dimension.DenominatorMode.BASE_SCOPE_TOTAL:
                    denominator = base_total
                else:
                    denominator = actual_total

                targeted_keys = set()

                for target in dimension.targets.filter(is_active=True).order_by("display_order", "key"):
                    targeted_keys.add(target.key)
                    bucket_actual = actual_map.get(target.key)

                    actual_value = Decimal(str(bucket_actual.actual_value)) if bucket_actual else Decimal("0")
                    holding_count = bucket_actual.holding_count if bucket_actual else 0

                    if target.target_value is not None:
                        target_value = Decimal(str(target.target_value))
                    elif target.target_percent is not None and base_total > 0:
                        target_value = (Decimal(str(target.target_percent)) * Decimal(str(base_total))).quantize(Decimal("0.01"))
                    else:
                        target_value = Decimal("0")

                    actual_percent = AllocationEngine._safe_percent(value=actual_value, denominator=denominator)
                    if target.target_percent is not None:
                        target_percent = Decimal(str(target.target_percent))
                    else:
                        target_percent = AllocationEngine._safe_percent(value=target_value, denominator=denominator)

                    rows.append(
                        AllocationGapResult(
                            run=run,
                            dimension=dimension,
                            target=target,
                            bucket_key_snapshot=target.key,
                            bucket_label_snapshot=target.label,
                            actual_value=actual_value.quantize(Decimal("0.01")),
                            target_value=target_value.quantize(Decimal("0.01")),
                            gap_value=(target_value - actual_value).quantize(Decimal("0.01")),
                            actual_percent=actual_percent,
                            target_percent=target_percent,
                            gap_percent=(target_percent - actual_percent),
                            holding_count=holding_count,
                        )
                    )

                # Include untargeted actual buckets so users can see hidden drift.
                for key, bucket_actual in actual_map.items():
                    if key in targeted_keys:
                        continue

                    actual_value = Decimal(str(bucket_actual.actual_value))
                    actual_percent = AllocationEngine._safe_percent(value=actual_value, denominator=denominator)

                    rows.append(
                        AllocationGapResult(
                            run=run,
                            dimension=dimension,
                            target=None,
                            bucket_key_snapshot=key,
                            bucket_label_snapshot=bucket_actual.label,
                            actual_value=actual_value.quantize(Decimal("0.01")),
                            target_value=Decimal("0.00"),
                            gap_value=(Decimal("0") - actual_value).quantize(Decimal("0.01")),
                            actual_percent=actual_percent,
                            target_percent=Decimal("0"),
                            gap_percent=(Decimal("0") - actual_percent),
                            holding_count=bucket_actual.holding_count,
                        )
                    )

            if rows:
                AllocationGapResult.objects.bulk_create(rows)

            AllocationRunService.mark_success(run=run)
            return run
        except Exception as exc:
            AllocationRunService.mark_failed(run=run, error=exc)
            raise
