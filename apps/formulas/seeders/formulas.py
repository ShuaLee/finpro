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
    # Dividend Formulas
    # ==================================================

    dividend_yield_trailing_formula, _ = Formula.objects.update_or_create(
        owner=None,
        identifier="dividend_yield_trailing",
        defaults={
            "title": "Trailing Dividend Yield",
            "expression": "trailing_12m_dividend / price",
            "decimal_places": 4,
        },
    )

    dividend_yield_forward_formula, _ = Formula.objects.update_or_create(
        owner=None,
        identifier="dividend_yield_forward",
        defaults={
            "title": "Forward Dividend Yield",
            "expression": "forward_annual_dividend / price",
            "decimal_places": 4,
        },
    )

    annual_dividend_income_formula, _ = Formula.objects.update_or_create(
        owner=None,
        identifier="annual_dividend_income",
        defaults={
            "title": "Annual Dividend Income",
            "expression": "forward_annual_dividend * quantity",
            "decimal_places": 2,
        },
    )

    trailing_dividend_income_formula, _ = Formula.objects.update_or_create(
        owner=None,
        identifier="trailing_dividend_income",
        defaults={
            "title": "Trailing Dividend Income",
            "expression": "trailing_12m_dividend * quantity",
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

    # ==================================================
    # FormulaDefinitions: DIVIDENDS (Equity only)
    # ==================================================

    FormulaDefinition.objects.update_or_create(
        owner=None,
        identifier="dividend_yield",
        asset_type=equity_type,
        defaults={
            "name": "Dividend Yield (Trailing)",
            "description": "Trailing 12-month dividend yield.",
            "formula": dividend_yield_trailing_formula,
            "dependency_policy": DependencyPolicy.AUTO_EXPAND,
            "is_system": True,
        },
    )

    FormulaDefinition.objects.update_or_create(
        owner=None,
        identifier="forward_dividend_yield",
        asset_type=equity_type,
        defaults={
            "name": "Forward Dividend Yield",
            "description": "Forward annual dividend yield.",
            "formula": dividend_yield_forward_formula,
            "dependency_policy": DependencyPolicy.AUTO_EXPAND,
            "is_system": True,
        },
    )

    FormulaDefinition.objects.update_or_create(
        owner=None,
        identifier="annual_dividend_income",
        asset_type=equity_type,
        defaults={
            "name": "Annual Dividend Income",
            "description": "Estimated annual dividend income.",
            "formula": annual_dividend_income_formula,
            "dependency_policy": DependencyPolicy.AUTO_EXPAND,
            "is_system": True,
        },
    )

    FormulaDefinition.objects.update_or_create(
        owner=None,
        identifier="trailing_dividend_income",
        asset_type=equity_type,
        defaults={
            "name": "Trailing Dividend Income",
            "description": "Trailing 12-month dividend income.",
            "formula": trailing_dividend_income_formula,
            "dependency_policy": DependencyPolicy.AUTO_EXPAND,
            "is_system": True,
        },
    )
