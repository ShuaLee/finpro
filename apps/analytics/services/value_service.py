from decimal import Decimal, InvalidOperation


class ValueResolverService:
    @staticmethod
    def get_text(*, holding_id, identifier, values_by_holding):
        if not identifier:
            return None
        return values_by_holding.get(holding_id, {}).get(identifier)

    @staticmethod
    def get_decimal(*, holding_id, identifier, values_by_holding):
        raw = ValueResolverService.get_text(
            holding_id=holding_id,
            identifier=identifier,
            values_by_holding=values_by_holding,
        )
        if raw in (None, ""):
            return Decimal("0")

        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")
