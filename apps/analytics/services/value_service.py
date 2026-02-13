from decimal import Decimal, InvalidOperation

from schemas.models import SchemaColumnValue


class ValueResolverService:
    @staticmethod
    def get_text(*, holding, identifier):
        scv = SchemaColumnValue.objects.filter(
            holding=holding,
            column__identifier=identifier,
        ).first()

        if not scv:
            return None

        return scv.value
    
    @staticmethod
    def get_decimal(*, holding, identifier):
        raw = ValueResolverService.get_text(
            holding=holding,
            identifier=identifier,
        )
        if raw in (None, ""):
            return Decimal("0")

        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")