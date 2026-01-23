from decimal import Decimal
from django.core.exceptions import ValidationError

from schemas.models import MasterConstraint, SchemaConstraint


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
        if master.applies_to == "integer":
            return master.default_integer
        if master.applies_to == "decimal":
            return master.default_decimal
        return master.default_string

    @staticmethod
    def _cast(master, raw):
        if raw in (None, "", "None"):
            return None

        try:
            if master.applies_to == "integer":
                value = int(raw)
                SchemaConstraintManager._check_bounds(
                    value, master.min_integer, master.max_integer
                )
                return value

            if master.applies_to == "decimal":
                value = Decimal(str(raw))
                SchemaConstraintManager._check_bounds(
                    value, master.min_decimal, master.max_decimal
                )
                return value

            return raw

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

        if master.applies_to == "integer":
            defaults.update(
                value_integer=value,
                min_integer=master.min_integer,
                max_integer=master.max_integer,
            )
        elif master.applies_to == "decimal":
            defaults.update(
                value_decimal=value,
                min_decimal=master.min_decimal,
                max_decimal=master.max_decimal,
            )
        else:
            defaults["value_string"] = value

        return defaults
