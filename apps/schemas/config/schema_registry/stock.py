from schemas.config.utils import schema_field
from decimal import Decimal

SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG = {
    "asset": {
        "ticker": schema_field(
            title="Ticker",
            data_type="string",
            field_path="stock.ticker",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={
                "character_limit": 10,
                "all_caps": True
            }
        ),
        "price": schema_field(
            title="Price",
            data_type="decimal",
            field_path="stock.price",
            is_default=True,
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            }
        ),
        "name": schema_field(
            title="Name",
            data_type="string",
            field_path="stock.name",
            constraints={"character_limit": 200}
        ),
        "currency": schema_field(
            title="Currency",
            data_type="string",
            field_path="stock.currency",
            constraints={
                "character_limit": 3,
                "character_minimum": 3,
                "all_caps": True
            }
        ),
    },
    "holding": {
        "quantity": schema_field(
            title="Quantity",
            data_type="decimal",
            field_path="quantity",
            is_default=True,
            is_deletable=False,
            constraints={"decimal_places": 4}
        ),
        "purchase_price": schema_field(
            title="Purchase Price",
            data_type="decimal",
            field_path="purchase_price",
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            }
        ),
    },
    "calculated": {
        "current_value_stock_fx": schema_field(
            title="Current Value - Stock FX",
            data_type="decimal",
            formula_method="current_value_stock_fx",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            }
        ),
        "current_value_profile_fx": schema_field(
            title="Current Value - Profile FX",
            data_type="decimal",
            formula_method="current_value_profile_fx",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            }
        ),
        "unrealized_gain": schema_field(
            title="Unrealized Gain",
            data_type="decimal",
            formula_method="get_unrealized_gain",
            is_editable=False,
            is_deletable=True,
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            }
        ),
    },
}

MANAGED_ACCOUNT_SCHEMA_CONFIG = {
    "custom": {
        "title": schema_field(
            title="Title",
            data_type="string",
            is_deletable=False,
            is_default=True,
            constraints={
                "character_limit": 200,
                "character_minimum": 0
            }
        ),
        "current_value": schema_field(
            title="Current Value",
            data_type="decimal",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            }
        ),
        "currency": schema_field(
            title="Currency",
            data_type="string",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={
                "character_limit": 3,
                "character_minimum": 3,
                "all_caps": True
            }
        ),
    },
}
