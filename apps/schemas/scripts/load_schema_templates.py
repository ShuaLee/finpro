from django.contrib.contenttypes.models import ContentType
from schemas.config import SCHEMA_CONFIG_REGISTRY
from schemas.models import SchemaColumnTemplate
from accounts.config.account_model_registry import ACCOUNT_MODEL_MAP
from schemas.config.utils import validate_constraints


def normalize_constraints(constraints, data_type):
    """
    Ensure default constraint values are set for each data type.
    Also validates using constraint definitions.
    """
    if not constraints:
        constraints = {}

    # Provide common defaults
    if data_type in ["decimal", "calculated"] and "decimal_places" not in constraints:
        constraints["decimal_places"] = 2

    # Validate using your central constraint validator
    validate_constraints(data_type, constraints)

    return constraints


def load_column_templates():
    for schema_type, variant_map in SCHEMA_CONFIG_REGISTRY.items():
        for variant_key, schema_dict in variant_map.items():
            account_model = ACCOUNT_MODEL_MAP.get(
                schema_type, {}).get(variant_key)
            if not account_model:
                print(
                    f"⚠️ No model registered for {schema_type} [{variant_key}]")
                continue

            account_model_ct = ContentType.objects.get_for_model(account_model)

            for source, columns in schema_dict.items():
                for source_field, config in columns.items():
                    SchemaColumnTemplate.objects.update_or_create(
                        account_model_ct=account_model_ct,
                        source=source,
                        source_field=source_field,
                        defaults={
                            "schema_type": schema_type,
                            "title": config["title"],
                            "data_type": config["data_type"],
                            "field_path": config.get("field_path"),
                            "is_editable": config.get("is_editable", True),
                            "is_default": config.get("is_default", True),
                            "is_deletable": config.get("is_deletable", True),
                            "is_system": config.get("is_system", False),
                            "formula_method": config.get("formula_method"),
                            "formula_expression": config.get("formula_expression"),
                            "constraints": normalize_constraints(config.get("constraints", {}), config["data_type"]),
                            "display_order": config.get("display_order", 0),
                        }
                    )

            print(f"✅ Loaded templates for: {schema_type} [{variant_key}]")


if __name__ == "__main__":
    load_column_templates()
