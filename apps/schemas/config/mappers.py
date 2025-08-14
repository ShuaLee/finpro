from typing import Dict, Any, Optional


def _constraints(spec: Dict[str, Any]) -> Dict[str, Any]:
    return spec.get("constraints", {}) or {}


def decimal_places_from_spec(spec: Dict[str, Any]) -> Optional[int]:
    # Central place to decide how decimal_places is derived
    return _constraints(spec).get("decimal_places")


def build_column_defaults_from_spec(spec: Dict[str, Any], display_order: int) -> Dict[str, Any]:
    """
    Normalize a schema-config spec into SchemaColumn(**defaults) kwargs.

    If you later decide to denormalize more items (e.g. storing character_limit on the column),
    do it here and nowhere else.
    """
    return {
        "title": spec["title"],
        "data_type": spec["data_type"],
        "field_path": spec.get("field_path"),
        "decimal_places": decimal_places_from_spec(spec),
        "editable": spec.get("editable", False),
        "is_deletable": spec.get("is_deletable", False),
        "is_system": spec.get("is_system", True),
        "display_order": display_order,
        "formula_method": spec.get("formula_method"),
        "formula_expression": spec.get("formula"),
    }
