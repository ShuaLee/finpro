from decimal import Decimal

# Define allowed constraints per data type
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
    # You can add 'integer', 'date', etc. if needed
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
                f"Invalid constraint '{key}' for data type '{data_type}'")
        elif not isinstance(value, expected_type if isinstance(expected_type, tuple) else (expected_type,)):
            errors.append(
                f"Constraint '{key}' for '{data_type}' must be of type {expected_type}, got {type(value)}"
            )

    if errors:
        raise ValueError("Invalid constraints: " + "; ".join(errors))


def schema_field(
    title: str,
    data_type: str,
    field_path: str = None,
    is_editable: bool = True,
    is_deletable: bool = True,
    is_default: bool = False,
    is_system: bool = True,
    constraints: dict = None,
    formula_method: str = None,
    formula_expression: str = None,
    source: str = None,
) -> dict:
    if constraints is None:
        constraints = {}

    # 🔒 Validate constraints
    validate_constraints(data_type, constraints)

    return {
        "title": title,
        "data_type": data_type,
        "field_path": field_path,
        "is_editable": is_editable,
        "is_deletable": is_deletable,
        "is_default": is_default,
        "is_system": is_system,
        "constraints": constraints,
        "formula_method": formula_method,
        "formula_expression": formula_expression,
        "source": source,
    }


def get_schema_column_defaults(schema_type: str, account_model_class=None):
    """
    Returns a list of default schema column definitions for a given asset type (e.g., 'stock').
    Optionally filters by a specific account model (e.g., SelfManagedAccount or ManagedAccount).
    Lazily imports the registry to avoid circular imports.
    """
    from . import SCHEMA_CONFIG_REGISTRY

    config = SCHEMA_CONFIG_REGISTRY.get(schema_type)
    if not config:
        raise ValueError(
            f"No schema config found for schema type: '{schema_type}'")

    # If the schema_type is nested by account model
    if isinstance(config, dict) and account_model_class:
        config = config.get(account_model_class)
        if not config:
            raise ValueError(
                f"No config found for schema_type '{schema_type}' and model '{account_model_class.__name__}'")

    columns = []
    display_counter = 1

    for source, fields in config.items():
        for source_field, meta in fields.items():
            if meta.get("is_default") is True:
                columns.append({
                    "source": source,
                    "source_field": source_field,
                    "title": meta["title"],
                    "data_type": meta["data_type"],
                    "field_path": meta.get("field_path"),
                    "is_editable": meta.get("is_editable", True),
                    "is_deletable": meta.get("is_deletable", True),
                    "is_system": meta.get("is_system", False),
                    "formula_expression": meta.get("formula_expression"),
                    "formula_method": meta.get("formula_method"),
                    "constraints": meta.get("constraints", {}),
                    "display_order": display_counter,
                })
                display_counter += 1

    return columns
