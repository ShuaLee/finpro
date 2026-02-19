from decimal import Decimal, InvalidOperation

from accounts.models import Holding
from schemas.models import SchemaColumnValue


class AllocationBaseValueService:
    @staticmethod
    def _to_decimal(raw):
        if raw in (None, ""):
            return Decimal("0")
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")

    @staticmethod
    def base_total_for_plan(*, plan) -> Decimal:
        holdings = Holding.objects.filter(account__portfolio=plan.portfolio)

        if plan.base_scope == plan.BaseScope.ACCOUNT_TYPE and plan.account_type_id:
            holdings = holdings.filter(account__account_type_id=plan.account_type_id)

        values = SchemaColumnValue.objects.filter(
            holding_id__in=holdings.values("id"),
            column__identifier=plan.base_value_identifier,
        ).values_list("value", flat=True)

        total = Decimal("0")
        for value in values:
            total += AllocationBaseValueService._to_decimal(value)
        return total
