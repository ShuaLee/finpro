from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import (
    SchemaColumnTemplateBehaviour,
)
from assets.models.core import AssetType
from formulas.models.formula_definition import FormulaDefinition


def seed_system_column_catalog():
    """
    Seed system-wide, optional schema column templates.

    These columns:
    - are NOT default
    - may be added to schemas by users
    - may apply to multiple asset types
    """

    # --------------------------------------------------
    # Asset types
    # --------------------------------------------------
    equity_type = AssetType.objects.get(slug="equity")
    crypto_type = AssetType.objects.get(slug="crypto")

    # ==================================================
    # Market Value (asset currency)
    # ==================================================

    market_value, _ = SchemaColumnTemplate.objects.update_or_create(
        template=None,  # GLOBAL system column
        identifier="market_value",
        defaults={
            "title": "Market Value",
            "data_type": "decimal",
            "is_system": True,
            "is_default": False,   # IMPORTANT
            "display_order": 0,    # catalog-only
        },
    )

    # ------------------------------
    # Equity behaviour
    # ------------------------------
    equity_def = FormulaDefinition.objects.get(
        identifier="market_value",
        asset_type=equity_type,
        owner__isnull=True,
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=market_value,
        asset_type=equity_type,
        defaults={
            "source": "formula",
            "formula_definition": equity_def,
        },
    )

    # ------------------------------
    # Crypto behaviour
    # ------------------------------
    crypto_def = FormulaDefinition.objects.get(
        identifier="market_value",
        asset_type=crypto_type,
        owner__isnull=True,
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=market_value,
        asset_type=crypto_type,
        defaults={
            "source": "formula",
            "formula_definition": crypto_def,
        },
    )
