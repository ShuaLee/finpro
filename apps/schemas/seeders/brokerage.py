from schemas.models.template import SchemaTemplate
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import (
    SchemaColumnTemplateBehaviour,
)

from accounts.models import AccountType
from assets.models.core import AssetType
from formulas.models.formula_definition import FormulaDefinition


def seed_brokerage_schema_template():
    """
    System schema template for brokerage accounts (equities only).

    Default columns:
    - quantity
    - price
    - current_value

    Optional system columns (e.g. market_value) are seeded separately.
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
    # Quantity (holding)
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
    # Price (asset)
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
    # Current Value (Formula: market_value * fx_rate)
    # ========================================================

    try:
        current_value_def = FormulaDefinition.objects.get(
            identifier="current_value",
            asset_type=equity_type,
            owner__isnull=True,
        )
    except FormulaDefinition.DoesNotExist:
        raise RuntimeError(
            "System FormulaDefinition 'current_value' for equity does not exist. "
            "Seed formulas before schema templates."
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
            "formula_definition": current_value_def,
        },
    )
