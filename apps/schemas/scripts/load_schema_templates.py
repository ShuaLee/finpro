from schemas.config import SCHEMA_CONFIG_REGISTRY
from schemas.models import SchemaColumnTemplate


def normalize_constraints(constraints, data_type):
    if not constraints:
        return {}

    # Ensure decimal_places is present if needed
    if data_type == "decimal" and "decimal_places" not in constraints:
        constraints["decimal_places"] = 2
    return constraints


def load_column_template():
    for asset_type, schema_dict in SCHEMA_CONFIG_REGISTRY.items():
        print(f"⏳ Loading templates for asset type: {asset_type}...")

        for source, columns in schema_dict.items():
            for source_field, config in columns.items():
                SchemaColumnTemplate.objects.update_or_create(
                    asset_type=asset_type,
                    source=source,
                    source_field=source_field,
                    defaults={
                        "title": config["title"],
                        "data_type": config["data_type"],
                        "field_path": config.get("field_path"),
                        "editable": config.get("editable", True),
                        "is_default": config.get("is_default", True),
                        "is_deletable": config.get("is_deletable", True),
                        "is_system": config.get("is_system", False),
                        "formula_method": config.get("formula_method"),
                        "formula_expression": config.get("formula_expression"),
                        "constraints": normalize_constraints(config.get("constraints", {}), config["data_type"]),
                        "display_order": config.get("display_order", 0),
                    }
                )
        print(f"✅ Loaded templates for {asset_type}")


if __name__ == "__main__":
    load_column_template()
