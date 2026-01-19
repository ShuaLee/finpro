from decimal import Decimal
from django.core.exceptions import ValidationError

from schemas.models.constraints import MasterConstraint, SchemaConstraint
from schemas.models.schema import SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager

import logging
logger = logging.getLogger(__name__)


class SchemaConstraintManager:
    """
    Creates SchemaConstraint rows for a SchemaColumn based on MasterConstraint rows.
    """

    # ======================================================================
    # MAIN ENTRY
    # ======================================================================
    @classmethod
    def create_from_master(cls, column, overrides=None):
        overrides = overrides or {}

        autodetected = cls._auto_detect_overrides(column)
        merged_overrides = {**autodetected, **overrides}

        masters = MasterConstraint.objects.filter(
            applies_to=column.data_type,
        )

        for master in masters:
            raw_value = merged_overrides.get(
                master.name, cls._get_master_default(master)
            )

            typed_value = cls._cast_and_validate(master, raw_value)

            defaults = {
                "label": master.label,
                "applies_to": master.applies_to,
                "is_editable": master.is_editable,
            }

            if master.applies_to == "integer":
                defaults["value_integer"] = typed_value
                defaults["min_integer"] = master.min_integer
                defaults["max_integer"] = master.max_integer

            elif master.applies_to == "decimal":
                defaults["value_decimal"] = typed_value
                defaults["min_decimal"] = master.min_decimal
                defaults["max_decimal"] = master.max_decimal

            else:
                defaults["value_string"] = typed_value

            SchemaConstraint.objects.get_or_create(
                column=column,
                name=master.name,
                defaults=defaults,
            )

        cls._refresh_scv_if_needed(column)

    # ======================================================================
    # TYPED FIELD HELPERS
    # ======================================================================
    @staticmethod
    def _get_master_default(master):
        if master.applies_to == "integer":
            return master.default_integer
        if master.applies_to == "decimal":
            return master.default_decimal
        return master.default_string

    @staticmethod
    def _cast_and_validate(master, raw_value):
        if raw_value in [None, "", "None"]:
            return None

        try:
            if master.applies_to == "integer":
                value = int(raw_value)
                SchemaConstraintManager._check_min_max(
                    value, master.min_integer, master.max_integer
                )
                return value

            elif master.applies_to == "decimal":
                value = Decimal(str(raw_value))
                SchemaConstraintManager._check_min_max(
                    value, master.min_decimal, master.max_decimal
                )
                return value

            else:
                return raw_value

        except Exception:
            raise ValidationError(
                f"Constraint '{master.name}' must be {master.applies_to}, "
                f"got '{raw_value}'."
            )

    @staticmethod
    def _check_min_max(value, min_val, max_val):
        if min_val is not None and value < min_val:
            raise ValidationError(f"Value {value} is below minimum {min_val}")
        if max_val is not None and value > max_val:
            raise ValidationError(f"Value {value} exceeds maximum {max_val}")

    # ======================================================================
    # AUTO-DETECTION (CRYPTO PRECISION ONLY)
    # ======================================================================
    @staticmethod
    def _auto_detect_overrides(column):
        """
        Currently only auto-detects crypto decimal precision.
        Explicit overrides always win.
        """
        overrides = {}

        if column.data_type != "decimal":
            return overrides

        asset = getattr(column, "_asset_context", None)
        if asset and getattr(asset, "crypto_detail", None):
            overrides["decimal_places"] = asset.crypto_detail.precision

        return overrides

    # ======================================================================
    # BUSINESS RULE VALIDATION (FOR FORMS ONLY)
    # ======================================================================
    @staticmethod
    def validate_business_rules_only(account, holding, cleaned_data):
        schema = account.active_schema
        if not schema:
            return cleaned_data

        for col in schema.columns.filter(source="holding"):
            field = col.source_field
            value = cleaned_data.get(field)

            if value is None:
                continue

            for constraint in col.constraints_set.all():
                typed = constraint.get_typed_value()
                if typed is None:
                    continue

                if constraint.name == "min_value" and Decimal(value) < Decimal(typed):
                    raise ValidationError({
                        field: (
                            f"{col.title}: value {value} "
                            f"is below minimum {typed}"
                        )
                    })

                if constraint.name == "max_value" and Decimal(value) > Decimal(typed):
                    raise ValidationError({
                        field: (
                            f"{col.title}: value {value} "
                            f"exceeds maximum {typed}"
                        )
                    })

        return cleaned_data

    # ======================================================================
    # SCV REFRESH
    # ======================================================================
    @classmethod
    def _refresh_scv_if_needed(cls, column):
        scvs = SchemaColumnValue.objects.filter(column=column)

        for scv in scvs:
            mgr = SchemaColumnValueManager(scv)
            mgr.refresh_display_value()
            scv.save(update_fields=["value", "is_edited"])
