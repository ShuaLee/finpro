from schemas.config.utils import schema_field
from decimal import Decimal

METALS_STORAGE_FACILITY_SCHEMA_CONFIG = {
    "asset": {
        "ticker": schema_field(
            title="Ticker",
            data_type="string",
            field_path="crypto.ticker",
            is_editable=False,
            is_deletable=False,
            is_system=True,
            constraints={
                "character_limit": 10
            }
        ),
        "price": schema_field(
            title="Price",
            data_type="decimal",
            field_path="crypto.price",
            is_default=True,
            is_deletable=False,
            is_system=True,
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            }
        ),
        "name": schema_field(
            title="Name",
            data_type="string",
            field_path="crypto.name",
            is_default=True,
            is_system=True,
            constraints={
                "character_limit": 200
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
            is_system=True,
            constraints={
                "decimal_places": 8,
                "min": Decimal("0")
            }
        ),
    }
}
