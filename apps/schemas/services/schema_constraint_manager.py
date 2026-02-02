from decimal import Decimal
from django.core.exceptions import ValidationError

from schemas.models import MasterConstraint, SchemaConstraint

from datetime import date


class SchemaConstraintManager:
    """
    Attaches SchemaConstraints based on MasterConstraints.

    PURE:
        - No recomputation
        - No schema traversal
        - No SCV logic
    """

    @classmethod
    def create_from_master(cls, column, overrides=None):
        overrides = overrides or {}

        masters = MasterConstraint.objects.filter(
            applies_to=column.data_type
        )

        for master in masters:
            raw_value = overrides.get(master.name, cls._default(master))
            typed_value = cls._cast(master, raw_value)
            defaults = cls._build_defaults(master, typed_value)

            SchemaConstraint.objects.get_or_create(
                column=column,
                name=master.name,
                defaults=defaults,
            )

    # ==========================================================
    # HELPERS
    # ==========================================================
    @staticmethod
    def _default(master):
        if master.applies_to in ("decimal", "percent"):
            return master.default_decimal
        if master.applies_to == "boolean":
            return master.default_boolean
        if master.applies_to == "date":
            return master.default_date
        return master.default_string

    @staticmethod
    def _cast(master, raw):
        if raw in (None, "", "None"):
            return None

        try:
            if master.name == "enum":
                return str(raw)

            if master.applies_to in ("decimal", "percent"):
                value = Decimal(str(raw))
                SchemaConstraintManager._check_bounds(
                    value, master.min_decimal, master.max_decimal
                )
                return value

            if master.applies_to == "boolean":
                if isinstance(raw, bool):
                    return raw
                val = str(raw).lower()
                if val in ("true", "1", "yes"):
                    return True
                if val in ("false", "0", "no"):
                    return False
                raise ValidationError("Invalid boolean value.")

            if master.applies_to == "date":
                return date.fromisoformat(str(raw))

            return str(raw)

        except ValidationError:
            raise
        except Exception:
            raise ValidationError(
                f"Invalid value for constraint '{master.name}': {raw}"
            )

    @staticmethod
    def _check_bounds(value, min_val, max_val):
        if min_val is not None and value < min_val:
            raise ValidationError(f"{value} < minimum {min_val}")
        if max_val is not None and value > max_val:
            raise ValidationError(f"{value} > maximum {max_val}")

    @staticmethod
    def _build_defaults(master, value):
        defaults = {
            "label": master.label,
            "applies_to": master.applies_to,
            "is_editable": False,
        }

        if master.applies_to in ("decimal", "percent"):
            defaults.update(
                value_decimal=value,
                min_decimal=master.min_decimal,
                max_decimal=master.max_decimal,
            )
        elif master.applies_to == "boolean":
            defaults["value_boolean"] = value
        elif master.applies_to == "date":
            defaults.update(
                value_date=value,
                min_date=master.min_date,
                max_date=master.max_date,
            )
        else:
            defaults["value_string"] = value

        return defaults
