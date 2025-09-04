from decimal import Decimal

CONSTRAINT_DEFINITIONS = {
    "decimal": {
        "decimal_places": int,
        "min": (int, float, Decimal),
        "max": (int, float, Decimal),
    },
    "calculated": {
        "decimal_places": int,
        "min": (int, float, Decimal),
        "max": (int, float, Decimal),
    },
    "string": {
        "character_limit": int,
        "character_minimum": int,
        "all_caps": bool,
    },
    # You can extend with 'date', 'datetime', etc. as needed
}


def validate_constraints(data_type: str, constraints: dict):
    """
    Validates that the given constraints dict is appropriate for the given data_type.
    """
    allowed = CONSTRAINT_DEFINITIONS.get(data_type, {})
    errors = []

    for key, value in constraints.items():
        expected_type = allowed.get(key)

        if expected_type is None:
            errors.append(
                f"Invalid constraint '{key}' for data type '{data_type}'"
            )
        elif not isinstance(value, expected_type if isinstance(expected_type, tuple) else (expected_type,)):
            errors.append(
                f"Constraint '{key}' for '{data_type}' must be of type {expected_type}, got {type(value)}"
            )

    if errors:
        raise ValueError("Invalid constraints: " + "; ".join(errors))
