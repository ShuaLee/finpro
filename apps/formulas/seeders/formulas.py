from formulas.models.formula import Formula
from formulas.models.formula_definition import (
    FormulaDefinition,
    DependencyPolicy,
)
from assets.models.core import AssetType


def seed_system_formulas():
    """
    Seed system formulas and formula definitions.

    System formulas are:
    - owner = None
    - immutable
    - referenced by schema templates
    """

    # ==================================================
    # Base Formula: quantity * price (asset currency)
    # ==================================================
    base_value_formula, _ = Formula.objects.update_or_create(
        owner=None,
        identifier="quantity_times_price",
        defaults={
            "title": "Quantity × Price",
            "expression": "quantity * price",
            "decimal_places": 2,
        },
    )

    # ==================================================
    # FX Formula: market_value * fx_rate
    # ==================================================
    fx_value_formula, _ = Formula.objects.update_or_create(
        owner=None,
        identifier="market_value_times_fx",
        defaults={
            "title": "Market Value × FX Rate",
            "expression": "market_value * fx_rate",
            "decimal_places": 2,
        },
    )

    # ==================================================
    # Asset Types
    # ==================================================
    equity_type = AssetType.objects.get(slug="equity")
    crypto_type = AssetType.objects.get(slug="cryptocurrency")

    # ==================================================
    # FormulaDefinitions: market_value (asset currency)
    # ==================================================
    for asset_type in (equity_type, crypto_type):
        FormulaDefinition.objects.update_or_create(
            owner=None,
            identifier="market_value",
            asset_type=asset_type,
            defaults={
                "name": "Market Value",
                "description": "Market value in the asset's native currency.",
                "formula": base_value_formula,
                "dependency_policy": DependencyPolicy.AUTO_EXPAND,
                "is_system": True,
            },
        )

    # ==================================================
    # FormulaDefinitions: current_value (profile currency)
    # ==================================================
    for asset_type in (equity_type, crypto_type):
        FormulaDefinition.objects.update_or_create(
            owner=None,
            identifier="current_value",
            asset_type=asset_type,
            defaults={
                "name": "Current Value",
                "description": "FX-adjusted market value in the user's currency.",
                "formula": fx_value_formula,
                "dependency_policy": DependencyPolicy.AUTO_EXPAND,
                "is_system": True,
            },
        )
