from django.core.exceptions import ValidationError
from decimal import Decimal

from schemas.models import SchemaColumnValue
from schemas.services.scv_refresh_service import SCVRefreshService


class SchemaColumnValueEditService:
    """
    Canonical entry point for user edits to SCVs.
    """

    @staticmethod
    def update_value(*, scv: SchemaColumnValue, raw_value):
        column = scv.column

        if not column.is_editable:
            raise ValidationError("This column is not editable.")

        behavior = column.behavior_for(
            scv.holding.asset.asset_type
        )

        if not behavior:
            raise ValidationError("No behavior defined for this column.")

        cast_value = SchemaColumnValueEditService._cast(
            raw_value, column.data_type
        )

        # ----------------------------------------
        # WRITE-THROUGH (holding-backed)
        # ----------------------------------------
        if behavior.source == "holding":
            setattr(
                scv.holding,
                behavior.source_field,
                cast_value,
            )
            scv.holding.save(update_fields=[behavior.source_field])

            scv.source = SchemaColumnValue.Source.SYSTEM
            scv.value = None
            scv.save(update_fields=["value", "source"])

        # ----------------------------------------
        # OVERRIDE (asset / formula / constant)
        # ----------------------------------------
        else:
            scv.value = cast_value
            scv.source = SchemaColumnValue.Source.USER
            scv.save(update_fields=["value", "source"])

        SCVRefreshService.holding_changed(scv.holding)

    # ----------------------------------------
    # CASTING
    # ----------------------------------------
    @staticmethod
    def _cast(raw, data_type):
        if raw is None:
            return None

        try:
            if data_type == "decimal":
                return Decimal(str(raw))
            if data_type == "integer":
                return int(raw)
            if data_type == "boolean":
                return bool(raw)
            return str(raw)
        except Exception:
            raise ValidationError(
                f"Invalid value for type '{data_type}'."
            )

    @staticmethod
    def revert_to_system(*, scv: SchemaColumnValue):
        if scv.source != SchemaColumnValue.Source.USER:
            return  # no-op

        scv.value = None
        scv.source = SchemaColumnValue.Source.SYSTEM
        scv.save(update_fields=["value", "source"])

        SCVRefreshService.holding_changed(scv.holding)
