from schemas.models.schema_column_category import SchemaColumnCategory


def seed_system_column_categories():
    """
    Seed canonical system SchemaColumnCategories.
    """

    categories = [
        {
            "identifier": "meta",
            "name": "Meta",
            "description": "Descriptive or identifying data",
            "display_order": 10,
        },
        {
            "identifier": "valuation",
            "name": "Valuation",
            "description": "Asset valuation and pricing",
            "display_order": 20,
        },
        {
            "identifier": "cash_flow",
            "name": "Cash Flow",
            "description": "Income and cash generation",
            "display_order": 30,
        },
    ]

    for data in categories:
        SchemaColumnCategory.objects.update_or_create(
            identifier=data["identifier"],
            defaults={
                "name": data["name"],
                "description": data["description"],
                "display_order": data["display_order"],
                "is_system": True,
            },
        )
