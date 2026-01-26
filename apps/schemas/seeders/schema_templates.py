"""
Seed SchemaTemplates for the system.

Currently seeds:
- Base Schema (fallback)
- Brokerage Schema (equities only)

Safe to re-run.
"""

from schemas.models.template import SchemaTemplate
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import (
    SchemaColumnTemplateBehaviour,
)

from accounts.models import AccountType
from assets.models.core import AssetType
from formulas.models.formula_definition import FormulaDefinition


# ============================================================
# ENTRY POINT
# ============================================================

def seed_schema_templates():
    """
    Main seeding entry point.
    """
    seed_base_schema_template()
    seed_brokerage_schema_template()


# ============================================================
# BASE SCHEMA TEMPLATE
# ============================================================

def seed_base_schema_template():
    """
    Base schema template.

    Used for:
    - custom account types
    - safe fallback

    No behaviours by design.
    """

    base_template, _ = SchemaTemplate.objects.update_or_create(
        account_type=None,
        defaults={
            "name": "Base Schema",
            "is_base": True,
            "is_active": True,
        },
    )

    # -------- Quantity (manual) --------
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

    # -------- Current Value (manual) --------
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

    # -------- Notes --------
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


# ============================================================
# BROKERAGE SCHEMA TEMPLATE (EQUITIES)
# ============================================================

def seed_brokerage_schema_template():
    """
    System schema template for brokerage accounts (equities only).
    """

    try:
        brokerage_type = AccountType.objects.get(slug="brokerage")
    except AccountType.DoesNotExist:
        raise RuntimeError(
            "AccountType with slug='brokerage' does not exist. "
            "Seed account types before schema templates."
        )

    try:
        equity_type = AssetType.objects.get(slug="equity")
    except AssetType.DoesNotExist:
        raise RuntimeError(
            "AssetType with slug='equity' does not exist. "
            "Seed asset types before schema templates."
        )

    template, _ = SchemaTemplate.objects.update_or_create(
        account_type=brokerage_type,
        defaults={
            "name": "Brokerage Account Schema",
            "is_base": False,
            "is_active": True,
        },
    )

    # ========================================================
    # Quantity
    # ========================================================

    quantity, _ = SchemaColumnTemplate.objects.update_or_create(
        template=template,
        identifier="quantity",
        defaults={
            "title": "Quantity",
            "data_type": "decimal",
            "is_system": True,
            "is_default": True,
            "display_order": 1,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=quantity,
        asset_type=equity_type,
        defaults={
            "source": "holding",
            "source_field": "quantity",
        },
    )

    # ========================================================
    # Price
    # ========================================================

    price, _ = SchemaColumnTemplate.objects.update_or_create(
        template=template,
        identifier="price",
        defaults={
            "title": "Price",
            "data_type": "decimal",
            "is_system": True,
            "is_default": True,
            "display_order": 2,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=price,
        asset_type=equity_type,
        defaults={
            "source": "asset",
            "source_field": "price",
        },
    )

    # ========================================================
    # Current Value (Formula)
    # ========================================================

    try:
        formula_def = FormulaDefinition.objects.get(
            identifier="current_value_equity"
        )
    except FormulaDefinition.DoesNotExist:
        raise RuntimeError(
            "FormulaDefinition with identifier='current_value_equity' "
            "does not exist. Seed formulas before schema templates."
        )

    current_value, _ = SchemaColumnTemplate.objects.update_or_create(
        template=template,
        identifier="current_value",
        defaults={
            "title": "Current Value",
            "data_type": "decimal",
            "is_system": True,
            "is_default": True,
            "display_order": 3,
        },
    )

    SchemaColumnTemplateBehaviour.objects.update_or_create(
        template=current_value,
        asset_type=equity_type,
        defaults={
            "source": "formula",
            "formula_definition": formula_def,
        },
    )
