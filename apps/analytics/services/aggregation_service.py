from collections import defaultdict
from decimal import Decimal

from analytics.services.dimension_resolver import DimensionResolverService
from analytics.services.value_service import ValueResolverService


class AggregationService:
    @staticmethod
    def aggregate_dimension(*, analytic, dimension, holdings):
        bucket_totals = defaultdict(Decimal)
        bucket_holding_ids = defaultdict(set)

        for holding in holdings:
            base_value = ValueResolverService.get_decimal(
                holding=holding,
                identifier=analytic.value_identifier,
            )

            if base_value == 0:
                continue

            contributions = DimensionResolverService.resolve_contributions(
                holding=holding,
                dimension=dimension,
            )

            for item in contributions:
                key = (item.bucket_id, item.label)
                bucket_totals[key] += (base_value * item.weight)
                bucket_holding_ids[key].add(holding.id)

        grand_total = sum(bucket_totals.values())

        rows = []
        for (bucket_id, label), total in bucket_totals.items():
            percentage = Decimal("0")
            if grand_total > 0:
                percentage = total / grand_total

            rows.append(
                {
                    "bucket_id": bucket_id,
                    "bucket_label": label,
                    "total_value": total,
                    "percentage": percentage,
                    "holding_count": len(bucket_holding_ids[(bucket_id, label)]),
                }
            )

        rows.sort(key=lambda r: r["total_value"], reverse=True)
        return rows
