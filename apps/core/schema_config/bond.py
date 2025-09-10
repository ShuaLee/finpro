from decimal import Decimal
from core.schema_config.utils import schema_field

BOND_SCHEMA_CONFIG = {
    "asset": {
        "symbol": schema_field("Symbol", "string", is_editable=False, is_default=True, constraints={"character_limit": 12}, display_order=1),
        "name": schema_field("Name", "string", is_editable=False, is_default=True, constraints={"character_limit": 200}, display_order=2),
        "issuer": schema_field("Issuer", "string", is_editable=False, is_default=False),
        "coupon_rate": schema_field("Coupon Rate (%)", "decimal", is_editable=False, is_default=False, constraints={"decimal_places": 2, "min": Decimal("0")}),
        "maturity_date": schema_field("Maturity Date", "date", is_editable=False, is_default=False),
        "rating": schema_field("Rating", "string", is_editable=False, is_default=False),
        "price": schema_field("Price", "decimal", is_editable=False, is_default=True, constraints={"decimal_places": 2, "min": Decimal("0")}, display_order=3),
    },
    "holding": {
        "quantity": schema_field("Quantity", "decimal", is_editable=True, is_default=True, constraints={"decimal_places": 2}, display_order=4),
        "purchase_price": schema_field("Purchase Price", "decimal", is_editable=True, is_default=True, constraints={"decimal_places": 2}, display_order=5),
        "purchase_date": schema_field("Purchase Date", "date", is_editable=True, is_default=True, display_order=6),
    },
    "calculated": {
        "current_value_bond_fx": schema_field("Current Value - Bond FX", "decimal", is_editable=False, is_default=False, formula_key="current_value_bond_fx", constraints={"decimal_places": 2, "min": Decimal("0")}),
    }
}