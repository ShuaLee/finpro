from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction

from schemas.models.schema_column_value import SchemaColumnValue
from schemas.services.schema_constraint_enum_resolver import (
    SchemaConstraintEnumResolver,
)
from schemas.services.scv_refresh_service import SCVRefreshService


class SchemaColumnValueEditService:
    """
    The ONLY allowed way to mutate SchemaColumnValues.
    """

    # ======================================================
    # PUBLIC ENTRY POINT
    # ======================================================
    @staticmethod
    @transaction.atomic
    def set_value(*, scv: SchemaColumnValue, raw_value):
        column = scv.column
        holding = scv.holding
        asset = holding.asset if holding else None
        asset_type = asset.asset_type if asset else None

        if not column.is_editable:
            raise ValidationError("This column is not editable.")

        behavior = column.behavior_for(asset_type)
        if not behavior:
            raise ValidationError(
                "Column has no behavior for this asset type."
            )

        # 1️⃣ Validate + normalize input
        value = SchemaColumnValueEditService._validate_value(
            column=column,
            raw_value=raw_value,
        )

        # 2️⃣ Apply edit
        if behavior.source == "holding":
            SchemaColumnValueEditService._write_to_holding(
                scv=scv,
                behavior=behavior,
                value=value,
            )
        else:
            SchemaColumnValueEditService._override_scv(
                scv=scv,
                value=value,
            )

        # 3️⃣ Recompute dependents
        if holding:
            SCVRefreshService.holding_changed(holding)

    # ======================================================
    # VALIDATION / NORMALIZATION
    # ======================================================
    @staticmethod
    def _validate_value(*, column, raw_value):
        # ---------------- ENUM ----------------
        enum_constraint = column.constraints.filter(name="enum").first()
        if enum_constraint:
            allowed = SchemaConstraintEnumResolver.resolve(
                enum_constraint,
                column=column,
            )
            if raw_value not in allowed:
                raise ValidationError(
                    f"Invalid value '{raw_value}'. Allowed: {allowed}"
                )

        # ---------------- TYPE CAST ----------------
        try:
            if column.data_type == "decimal":
                value = Decimal(str(raw_value))

            elif column.data_type == "percent":
                # Accept: 8, 8.0, "8%", "8.00%"
                if raw_value is None:
                    raise ValidationError("Percent value is required.")

                raw_str = str(raw_value).strip()

                # Strip percent sign if present
                if raw_str.endswith("%"):
                    raw_str = raw_str[:-1].strip()

                try:
                    value = Decimal(raw_str) / Decimal("100")
                except Exception:
                    raise ValidationError(
                        "Invalid percent value. Enter a number like 8 or 8.5 (for 8%)."
                    )

            elif column.data_type == "integer":
                value = int(raw_value)

            elif column.data_type == "boolean":
                value = SchemaColumnValueEditService._cast_boolean(raw_value)

            else:
                value = str(raw_value)

        except Exception:
            raise ValidationError(
                f"Invalid value for data type '{column.data_type}'."
            )

        # ---------------- CONSTRAINTS ----------------
        for constraint in column.constraints.all():
            constraint.validate(value)

        return value

    @staticmethod
    def _cast_boolean(raw):
        if isinstance(raw, bool):
            return raw
        val = str(raw).strip().lower()
        if val in ("true", "1", "yes"):
            return True
        if val in ("false", "0", "no"):
            return False
        raise ValidationError("Invalid boolean value.")

    # ======================================================
    # WRITE PATHS
    # ======================================================
    @staticmethod
    def _write_to_holding(*, scv, behavior, value):
        holding = scv.holding

        if not behavior.source_field:
            raise ValidationError(
                "Holding-backed column has no source_field."
            )

        target = holding
        parts = behavior.source_field.split("__")

        for part in parts[:-1]:
            target = getattr(target, part, None)
            if target is None:
                raise ValidationError(
                    f"Invalid source_field path '{behavior.source_field}'."
                )

        setattr(target, parts[-1], value)
        target.save()

        scv.value = None
        scv.source = SchemaColumnValue.Source.SYSTEM
        scv.save(update_fields=["value", "source"])

    @staticmethod
    def _override_scv(*, scv, value):
        scv.value = value
        scv.source = SchemaColumnValue.Source.USER
        scv.save(update_fields=["value", "source"])

    # ======================================================
    # REVERT
    # ======================================================
    @staticmethod
    def revert(*, scv: SchemaColumnValue):
        if scv.source != SchemaColumnValue.Source.USER:
            return

        holding = scv.holding
        asset = holding.asset if holding else None
        asset_type = asset.asset_type if asset else None

        behavior = scv.column.behavior_for(asset_type)
        if behavior and behavior.source == "formula":
            return

        scv.value = None
        scv.source = SchemaColumnValue.Source.SYSTEM
        scv.save(update_fields=["value", "source"])

        if holding:
            SCVRefreshService.holding_changed(holding)
