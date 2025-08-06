from . import SCHEMA_CONFIG_REGISTRY
from schemas.models import CustomAssetSchemaConfig


def get_schema_column_defaults(asset_type):
    config = SCHEMA_CONFIG_REGISTRY.get(asset_type, {})
    columns = []
    display_counter = 0

    for source, fields in config.items():
        for field_key, meta in fields.items():
            if meta.get("is_default"):
                columns.append({
                    "title": meta.get("title", field_key.replace("_", " ").title()),
                    "source": source,
                    "source_field": field_key,
                    "data_type": meta["data_type"],
                    "editable": meta.get("editable", True),
                    "is_deletable": meta.get("is_deletable", True),
                    "decimal_places": meta.get("decimal_places"),
                    "formula": meta.get("formula"),
                    "formula_expression": meta.get("formula_expression"),
                    "formula_method": meta.get("formula_method"),
                    "display_order": display_counter,
                })
                display_counter += 1
    return columns


def get_asset_schema_config(schema_type):
    """
    Returns schema config for a given schema type.
    Checks DB override first, then falls back to static registry.
    """
    db_config = CustomAssetSchemaConfig.objects.filter(
        asset_type=schema_type).first()
    if db_config:
        return db_config.config

    return SCHEMA_CONFIG_REGISTRY.get(schema_type, {})
