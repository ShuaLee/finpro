from schemas.services.schema_template_manager import SchemaTemplateManager
from decimal import Decimal

METALS_ACCOUNT_SCHEMA_CONFIG = {
    "asset": {
        "ticker": SchemaTemplateManager.schema_field(
            title="Ticker",
            data_type="string",
            source_field="ticker",
            is_default=True,
            is_editable=False,
            is_deletable=False,
            is_system=True,
            constraints={
                "character_limit": 10
            },
            display_order=1,
        ),
        "price": SchemaTemplateManager.schema_field(
            title="Price",
            data_type="decimal",
            source_field="price",
            is_default=True,
            is_deletable=False,
            is_system=True,
            constraints={
                "decimal_places": 2,
                "min": Decimal("0")
            },
            display_order=2,
        ),
        "name": SchemaTemplateManager.schema_field(
            title="Name",
            data_type="string",
            source_field="name",
            is_default=True,
            is_system=True,
            constraints={
                "character_limit": 200
            },
            display_order=3,
        ),
    },
    "holding": {
        "quantity": SchemaTemplateManager.schema_field(
            title="Quantity",
            data_type="decimal",
            source_field="quantity",
            is_default=True,
            is_deletable=False,
            is_system=True,
            constraints={
                "decimal_places": 8,
                "min": Decimal("0")
            },
            display_order=4,
        ),
    }
}
