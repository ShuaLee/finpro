from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from django.core.exceptions import ValidationError


def validate_value_against_constraints(value, data_type, constraints):
    if not constraints:
        return

    if data_type == "decimal":
        try:
            value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValidationError("Invalid decimal value.")

        # decimal_places
        if "decimal_places" in constraints:
            quant = Decimal(f"1.{'0' * constraints['decimal_places']}")
            if value != value.quantize(quant, rounding=ROUND_HALF_UP):
                raise ValidationError(
                    f"Must have at most {constraints['decimal_places']} decimal places."
                )

        # min
        if "min" in constraints:
            if value < Decimal(str(constraints["min"])):
                raise ValidationError(
                    f"Must be at least {constraints['min']}.")

        # max (optional support)
        if "max" in constraints:
            if value > Decimal(str(constraints["max"])):
                raise ValidationError(f"Must be at most {constraints['max']}.")

    elif data_type == "string":
        if not isinstance(value, str):
            raise ValidationError("Value must be a string.")

        if "character_limit" in constraints:
            if len(value) > constraints["character_limit"]:
                raise ValidationError(
                    f"Cannot exceed {constraints['character_limit']} characters.")

        if "character_minimum" in constraints:
            if len(value) < constraints["character_minimum"]:
                raise ValidationError(
                    f"Must be at least {constraints['character_minimum']} characters.")

        if constraints.get("all_caps") and value != value.upper():
            raise ValidationError("Must be all uppercase.")
