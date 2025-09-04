from schemas.services.schema_template_manager import SchemaTemplateManager
from decimal import Decimal

SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG = {
    "asset": {
        "ticker": SchemaTemplateManager.schema_field(
            title="Ticker",
            data_type="string",
            source_field="ticker",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={
                "character_limit": 10,
                "all_caps": True
            },
            display_order=1,
        ),
        "price": SchemaTemplateManager.schema_field(
            title="Price",
            data_type="decimal",
            source_field="price",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            },
            display_order=4,
        ),
        "name": SchemaTemplateManager.schema_field(
            title="Name",
            data_type="string",
            source_field="name",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={"character_limit": 200},
            display_order=2,
        ),
        "currency": SchemaTemplateManager.schema_field(
            title="Currency",
            data_type="string",
            source_field="currency",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={
                "character_limit": 3,
                "character_minimum": 3,
                "all_caps": True
            },
            display_order=3,
        ),
    },
    "holding": {
        "quantity": SchemaTemplateManager.schema_field(
            title="Quantity",
            data_type="decimal",
            source_field="quantity",
            is_editable=True,
            is_default=True,
            is_deletable=False,
            constraints={"decimal_places": 4},
            display_order=5,
        ),
        "purchase_price": SchemaTemplateManager.schema_field(
            title="Purchase Price",
            data_type="decimal",
            source_field="purchase_price",
            is_editable=True,
            is_deletable=False,
            is_default=True,
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            },
            display_order=6,
        ),
    },
    "calculated": {
        "current_value_stock_fx": SchemaTemplateManager.schema_field(
            title="Current Value - Stock FX",
            data_type="decimal",
            formula_key="current_value_stock_fx",  # 🔑 references formula
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={"decimal_places": 2, "min": Decimal("0")},
            display_order=7,
        ),
        "current_value_profile_fx": SchemaTemplateManager.schema_field(
            title="Current Value - Profile FX",
            data_type="decimal",
            formula_key="current_value_profile_fx",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={"decimal_places": 2, "min": Decimal("0")},
            display_order=8,
        ),
        "unrealized_gain": SchemaTemplateManager.schema_field(
            title="Unrealized Gain",
            data_type="decimal",
            formula_key="unrealized_gain",
            is_editable=False,
            is_deletable=True,
            is_default=False,
            constraints={"decimal_places": 2, "min": Decimal("0")},
        ),
    },
}

MANAGED_ACCOUNT_SCHEMA_CONFIG = {
    "custom": {
        "title": SchemaTemplateManager.schema_field(
            title="Title",
            data_type="string",
            is_deletable=False,
            is_default=True,
            constraints={"character_limit": 200, "character_minimum": 0},
            display_order=1,
        ),
        "current_value": SchemaTemplateManager.schema_field(
            title="Current Value",
            data_type="decimal",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={"decimal_places": 2, "min": Decimal("0")},
            display_order=2,
        ),
        "currency": SchemaTemplateManager.schema_field(
            title="Currency",
            data_type="string",
            is_editable=False,
            is_deletable=False,
            is_default=True,
            constraints={"character_limit": 3,
                         "character_minimum": 3, "all_caps": True},
            display_order=3,
        ),
    },
}
