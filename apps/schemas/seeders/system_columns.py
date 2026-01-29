from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import (
    SchemaColumnTemplateBehaviour,
)
from schemas.models.schema_column_category import SchemaColumnCategory
from assets.models.core import AssetType
from formulas.models.formula_definition import FormulaDefinition


def seed_system_column_catalog():
    """
    Seed global system SchemaColumnTemplates.

    These define WHAT columns exist in the system.
    Asset-type applicability is defined exclusively
    by SchemaColumnTemplateBehaviour.
    """

    equity = AssetType.objects.get(slug="equity")
    crypto = AssetType.objects.get(slug="cryptocurrency")

    # --------------------------------------------------
    # Categories (must already be seeded)
    # --------------------------------------------------
    meta = SchemaColumnCategory.objects.get(identifier="meta")
    valuation = SchemaColumnCategory.objects.get(identifier="valuation")

    # ==================================================
    # Quantity (Meta)
    # ==================================================

    quantity, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="quantity",
        defaults={
            "title": "Quantity",
            "description": "Number of units held",
            "data_type": "decimal",
            "is_system": True,
            "category": meta,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=quantity,
            asset_type=asset_type,
            defaults={
                "source": "holding",
                "source_field": "quantity",
            },
        )

    # ==================================================
    # Asset Currency (Meta)
    # ==================================================

    asset_currency, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="asset_currency",
        defaults={
            "title": "Asset Currency",
            "description": "Currency the asset is denominated in",
            "data_type": "string",
            "is_system": True,
            "category": meta,
        },
    )

    # --------------------------------------------------
    # Equity behavior
    # --------------------------------------------------
    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=asset_currency,
        asset_type=equity,
        defaults={
            "source": "asset",
            "source_field": "extension__currency__code",
        },
    )

    # --------------------------------------------------
    # Crypto behavior
    # --------------------------------------------------
    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=asset_currency,
        asset_type=crypto,
        defaults={
            "source": "asset",
            "source_field": "extension__currency__code",
        },
    )

    # ==================================================
    # Price (Valuation)
    # ==================================================

    price, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="price",
        defaults={
            "title": "Price",
            "description": "Current asset price",
            "data_type": "decimal",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=price,
            asset_type=asset_type,
            defaults={
                "source": "asset",
                "source_field": "price__price",
            },
        )

    # ==================================================
    # Market Value (asset currency) – Valuation
    # ==================================================

    market_value, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="market_value",
        defaults={
            "title": "Market Value",
            "description": "Market value in asset currency",
            "data_type": "decimal",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        definition = FormulaDefinition.objects.get(
            identifier="market_value",
            asset_type=asset_type,
            owner__isnull=True,
        )

        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=market_value,
            asset_type=asset_type,
            defaults={
                "source": "formula",
                "formula_definition": definition,
            },
        )

    # ==================================================
    # Current Value (profile currency) – Valuation
    # ==================================================

    current_value, _ = SchemaColumnTemplate.objects.update_or_create(
        identifier="current_value",
        defaults={
            "title": "Current Value",
            "description": "Market value converted to profile currency",
            "data_type": "decimal",
            "is_system": True,
            "category": valuation,
        },
    )

    for asset_type in (equity, crypto):
        definition = FormulaDefinition.objects.get(
            identifier="current_value",
            asset_type=asset_type,
            owner__isnull=True,
        )

        SchemaColumnTemplateBehaviour.objects.update_or_create(
            template=current_value,
            asset_type=asset_type,
            defaults={
                "source": "formula",
                "formula_definition": definition,
            },
        )
