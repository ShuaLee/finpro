from schemas.config.utils import schema_field
from decimal import Decimal

# System-wide default starter set for *any* custom:<slug> schema
CUSTOM_DEFAULT_SCHEMA_CONFIG = {
    "holding": {
        "title": schema_field(
            title="Title",
            data_type="string",
            is_default=True,
            is_deletable=False,
            is_system=True,
            constraints={"character_limit": 200},
        ),
        "quantity": schema_field(
            title="Quantity",
            data_type="decimal",
            is_default=True,
            is_deletable=True,
            is_system=True,
            constraints={"decimal_places": 2, "min": Decimal("0")},
        ),
        "current_estimated_value": schema_field(
            title="Current Estimated Value",
            data_type="decimal",
            is_default=True,
            is_deletable=True,
            is_system=True,
            constraints={"decimal_places": 2, "min": Decimal("0")},
        ),
        # optional note field
        "notes": schema_field(
            title="Notes",
            data_type="string",
            is_default=False,  # include if you want it on by default
            is_deletable=True,
            is_system=True,
            constraints={"character_limit": 500},
        ),
    }
}