from schemas.models.template import SchemaTemplate
from schemas.models.schema_column_template import SchemaColumnTemplate


def seed_base_schema():
    base_template, _ = SchemaTemplate.objects.update_or_create(
        account_type=None,
        defaults={
            "name": "Base Schema",
            "is_base": True,
            "is_active": True,
        },
    )

    SchemaColumnTemplate.objects.update_or_create(
        template=base_template,
        identifier="quantity",
        defaults={
            "title": "Quantity",
            "data_type": "decimal",
            "is_system": True,
            "is_default": True,
            "display_order": 1,
        },
    )

    SchemaColumnTemplate.objects.update_or_create(
        template=base_template,
        identifier="current_value",
        defaults={
            "title": "Current Value",
            "data_type": "decimal",
            "is_system": True,
            "is_default": True,
            "display_order": 2,
        },
    )

    SchemaColumnTemplate.objects.update_or_create(
        template=base_template,
        identifier="notes",
        defaults={
            "title": "Notes",
            "data_type": "string",
            "is_system": True,
            "is_default": True,
            "display_order": 3,
        },
    )
