from assets.models.core import AssetType
from formulas.models.formula import Formula
from formulas.models.formula_definition import DependencyPolicy, FormulaDefinition


def _resolve_crypto_asset_type():
    for slug in ("crypto", "cryptocurrency"):
        asset_type = AssetType.objects.filter(slug=slug).first()
        if asset_type:
            return asset_type
    raise AssetType.DoesNotExist("No crypto asset type found (expected slug 'crypto').")


def _seed_formulas():
    """
    Underlying arithmetic formulas reused by semantic FormulaDefinitions.
    """
    formulas = {
        "quantity_times_price": {
            "title": "Quantity x Price",
            "expression": "quantity * price",
            "decimal_places": 2,
        },
        "market_value_times_fx": {
            "title": "Market Value x FX Rate",
            "expression": "market_value * fx_rate",
            "decimal_places": 2,
        },
        "quantity_times_avg_price_times_fx": {
            "title": "Quantity x Average Purchase Price x FX Rate",
            "expression": "quantity * average_purchase_price * fx_rate",
            "decimal_places": 2,
        },
        "current_value_minus_cost_basis": {
            "title": "Current Value - Cost Basis",
            "expression": "current_value - cost_basis",
            "decimal_places": 2,
        },
        "unrealized_gain_over_cost_basis": {
            "title": "Unrealized Gain / Cost Basis",
            "expression": "unrealized_gain / cost_basis",
            "decimal_places": 6,
        },
    }

    out: dict[str, Formula] = {}
    for identifier, data in formulas.items():
        formula, _ = Formula.objects.update_or_create(
            owner=None,
            identifier=identifier,
            defaults=data,
        )
        out[identifier] = formula
    return out


def _seed_definitions_for_asset_type(*, asset_type, formulas):
    """
    Semantic formula definitions consumed by schemas.
    """
    definitions = {
        "market_value": {
            "name": "Market Value",
            "description": "Market value in the asset's native currency.",
            "formula": formulas["quantity_times_price"],
            "dependency_policy": DependencyPolicy.AUTO_EXPAND,
        },
        "current_value": {
            "name": "Current Value",
            "description": "Market value converted to profile currency.",
            "formula": formulas["market_value_times_fx"],
            "dependency_policy": DependencyPolicy.AUTO_EXPAND,
        },
        "cost_basis": {
            "name": "Cost Basis",
            "description": "Cost basis converted to profile currency.",
            "formula": formulas["quantity_times_avg_price_times_fx"],
            "dependency_policy": DependencyPolicy.AUTO_EXPAND,
        },
        "unrealized_gain": {
            "name": "Unrealized Gain",
            "description": "Current value minus cost basis in profile currency.",
            "formula": formulas["current_value_minus_cost_basis"],
            "dependency_policy": DependencyPolicy.AUTO_EXPAND,
        },
        "unrealized_gain_pct": {
            "name": "Unrealized Gain %",
            "description": "Unrealized gain divided by cost basis.",
            "formula": formulas["unrealized_gain_over_cost_basis"],
            "dependency_policy": DependencyPolicy.AUTO_EXPAND,
        },
    }

    for identifier, data in definitions.items():
        FormulaDefinition.objects.update_or_create(
            owner=None,
            identifier=identifier,
            asset_type=asset_type,
            defaults={
                "name": data["name"],
                "description": data["description"],
                "formula": data["formula"],
                "dependency_policy": data["dependency_policy"],
                "is_system": True,
            },
        )


def seed_system_formulas():
    """
    Seed all system formulas and formula definitions.
    """
    formulas = _seed_formulas()
    equity_type = AssetType.objects.get(slug="equity")
    crypto_type = _resolve_crypto_asset_type()
    for asset_type in (equity_type, crypto_type):
        _seed_definitions_for_asset_type(asset_type=asset_type, formulas=formulas)
