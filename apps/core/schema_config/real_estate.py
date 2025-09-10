from core.schema_config.utils import schema_field

REAL_ESTATE_SCHEMA_CONFIG = {
    "asset": {
        "symbol": schema_field("Symbol", "string", is_editable=True, is_default=True, constraints={"character_limit": 20}, display_order=1),
        "name": schema_field("Property Name", "string", is_editable=True, is_default=True, constraints={"character_limit": 200}, display_order=2),
        "location": schema_field("Location", "string", is_editable=True, is_default=False),
        "property_type": schema_field("Property Type", "string", is_editable=True, is_default=False),
        "estimated_value": schema_field("Estimated Value", "decimal", is_editable=True, is_default=True, constraints={"decimal_places": 2}, display_order=3),
    },
    "holding": {
        "purchase_price": schema_field("Purchase Price", "decimal", is_editable=True, is_default=True, constraints={"decimal_places": 2}, display_order=4),
        "purchase_date": schema_field("Purchase Date", "date", is_editable=True, is_default=True, display_order=5),
    },
    "calculated": {
        "unrealized_gain": schema_field("Unrealized Gain", "decimal", formula_key="unrealized_gain", is_editable=False, is_default=False, constraints={"decimal_places": 2}),
    }
}
