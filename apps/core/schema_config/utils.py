from schemas.validators import validate_constraints


def schema_field(
    title: str,
    data_type: str,
    source_field: str = None,
    is_editable: bool = True,
    is_deletable: bool = True,
    is_default: bool = False,
    is_system: bool = True,
    constraints: dict = None,
    source: str = None,
    formula_key: str = None,
    display_order: int = None,
) -> dict:
    """
    Helper for defining schema field configuration blocks.
    """
    constraints = constraints or {}

    validate_constraints(data_type, constraints)

    if is_default and display_order is None:
        raise ValueError(
            f"Default column '{title}' must define an explicit display_order."
        )

    return {
        "title": title,
        "data_type": data_type,
        "source_field": source_field,
        "is_editable": is_editable,
        "is_deletable": is_deletable,
        "is_default": is_default,
        "is_system": is_system,
        "constraints": constraints,
        "source": source,
        "formula_key": formula_key,
        "display_order": display_order if is_default else None,
    }
