from decimal import Decimal
from core.schema_config.utils import schema_field

CUSTOM_SCHEMA_CONFIG = {
    "asset": {
        "symbol": schema_field(
            title="Symbol",
            data_type="string",
            is_editable=True,
            is_deletable=False,
            is_default=True,
            constraints={"character_limit": 10},
            display_order=1,
        ),
        "name": schema_field(
            title="Name",
            data_type="string",
            is_editable=True,
            is_deletable=False,
            is_default=True,
            constraints={"character_limit": 200},
            display_order=2,
        ),
        "description": schema_field(
            title="Description",
            data_type="string",
            is_editable=True,
            is_default=False,
        ),
    },
    "holding": {
        "quantity": schema_field(
            title="Quantity",
            data_type="decimal",
            is_editable=True,
            is_deletable=False,
            is_default=True,
            constraints={"decimal_places": 2},
            display_order=3,
        ),
        "purchase_price": schema_field(
            title="Purchase Price",
            data_type="decimal",
            is_editable=True,
            is_deletable=False,
            is_default=True,
            constraints={"decimal_places": 2, "min": Decimal("0")},
            display_order=4,
        ),
        "purchase_date": schema_field(
            title="Purchase Date",
            data_type="date",
            is_editable=True,
            is_default=True,
            display_order=5,
        ),
    },
    "calculated": {
        "current_value_custom_fx": schema_field(
            title="Current Value - Custom FX",
            data_type="decimal",
            formula_key="current_value_custom_fx",
            is_editable=False,
            is_deletable=True,
            is_default=False,
            constraints={"decimal_places": 2, "min": Decimal("0")},
            display_order=6,
        ),
    },
}
