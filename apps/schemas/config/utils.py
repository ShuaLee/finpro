from . import SCHEMA_CONFIG_REGISTRY
from schemas.config.mappers import decimal_places_from_spec
from django.apps import apps


def _CustomAssetSchemaConfig():
    # Lazy model import to avoid circulars
    return apps.get_model('schemas', 'CustomAssetSchemaConfig')


def get_column_constraints(schema_type: str, source: str, field: str) -> dict:
    cfg = get_asset_schema_config(schema_type)
    meta = (cfg.get(source, {}) or {}).get(field, {}) or {}
    return meta.get("constraints", {}) or {}


def get_schema_column_defaults(schema_type: str, account_model_class=None):
    """
    Returns a list of default schema column definitions for a given asset type (e.g., 'stock').
    Optionally filters by a specific account model (e.g., SelfManagedAccount or ManagedAccount).
    """
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
        for field_key, meta in fields.items():
            if meta.get("is_default") is True:
                columns.append({
                    "title": meta.get("title", field_key.replace("_", " ").title()),
                    "source": source,
                    "source_field": field_key,
                    "data_type": meta["data_type"],
                    "field_path": meta.get("field_path"),
                    "editable": meta.get("editable", True),
                    "is_deletable": meta.get("is_deletable", True),
                    "is_system": meta.get("is_system", False),
                    "formula_expression": meta.get("formula_expression"),
                    "formula_method": meta.get("formula_method"),
                    "constraints": meta.get("constraints", {}),
                    "display_order": display_counter,
                })
                display_counter += 1

    return columns


def get_asset_schema_config(schema_type):
    """
    Returns schema config for a given schema type.
    Checks DB override first, then falls back to static registry.
    """
    CustomAssetSchemaConfig = _CustomAssetSchemaConfig()
    db_config = CustomAssetSchemaConfig.objects.filter(
        asset_type=schema_type).first()
    if db_config:
        return db_config.config

    return SCHEMA_CONFIG_REGISTRY.get(schema_type, {})


def get_available_config_columns(schema):
    """
    Returns a list of config-based columns that have not been added to the schema yet.
    Each item in the list is a (source, source_field, meta) tuple.
    """
    config = get_asset_schema_config(schema.schema_type)
    existing = {(col.source, col.source_field) for col in schema.columns.all()}

    available = []
    for source, fields in config.items():
        for field_key, meta in fields.items():
            if (source, field_key) not in existing:
                available.append((source, field_key, meta))
    return available


def get_serialized_available_columns(schema):
    """
    Returns config columns not yet added, formatted for API response.
    """
    return [
        {
            "title": meta.get("title", field.replace("_", " ").title()),
            "source": source,
            "source_field": field,
            "data_type": meta.get("data_type"),
            "decimal_places": decimal_places_from_spec(meta),
            # if you want to surface for UI
            "constraints": meta.get("constraints", {}),
            "description": f"{source}.{field}",
            "is_deletable": meta.get("is_deletable", True),
            "editable": meta.get("editable", True),
        }
        for source, field, meta in get_available_config_columns(schema)
    ]
