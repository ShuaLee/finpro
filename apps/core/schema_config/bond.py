from decimal import Decimal
from core.schema_config.utils import schema_field

BOND_SCHEMA_CONFIG = {
    "asset": {
        # --- Identification ---
        "symbol": schema_field(
            "Symbol", "string",
            is_editable=False, is_default=True,
            constraints={"character_limit": 12},
            display_order=1,
        ),
        "name": schema_field(
            "Name", "string",
            is_editable=False, is_default=True,
            constraints={"character_limit": 200},
            display_order=2,
        ),
        "issuer": schema_field("Issuer", "string", is_editable=False, is_default=False),
        "cusip": schema_field("CUSIP", "string", is_editable=False, is_default=False),
        "isin": schema_field("ISIN", "string", is_editable=False, is_default=False),
        "bond_type": schema_field("Bond Type", "string", is_editable=False, is_default=False),

        # --- Coupon & Dates ---
        "coupon_rate": schema_field(
            "Coupon Rate (%)", "decimal",
            is_editable=False, is_default=False,
            constraints={"decimal_places": 2, "min": Decimal("0")},
        ),
        "coupon_frequency": schema_field("Coupon Frequency", "string", is_editable=False, is_default=False),
        "issue_date": schema_field("Issue Date", "date", is_editable=False, is_default=False),
        "maturity_date": schema_field("Maturity Date", "date", is_editable=False, is_default=False),
        "call_date": schema_field("Call Date", "date", is_editable=False, is_default=False),

        # --- Market Data ---
        "last_price": schema_field(
            "Last Price", "decimal",
            is_editable=False, is_default=True,
            constraints={"decimal_places": 2, "min": Decimal("0")},
            display_order=3,
        ),
        "yield_to_maturity": schema_field("Yield to Maturity (%)", "decimal", is_editable=False, is_default=False),
        "yield_to_call": schema_field("Yield to Call (%)", "decimal", is_editable=False, is_default=False),
        "current_yield": schema_field("Current Yield (%)", "decimal", is_editable=False, is_default=False),
        "accrued_interest": schema_field("Accrued Interest", "decimal", is_editable=False, is_default=False),

        # --- Credit & Risk ---
        "rating": schema_field("Rating", "string", is_editable=False, is_default=False),
        "duration": schema_field("Duration", "decimal", is_editable=False, is_default=False),
        "convexity": schema_field("Convexity", "decimal", is_editable=False, is_default=False),

        # --- Size & Liquidity ---
        "par_value": schema_field("Par Value", "decimal", is_editable=False, is_default=False),
        "issue_size": schema_field("Issue Size", "integer", is_editable=False, is_default=False),
        "outstanding_amount": schema_field("Outstanding Amount", "integer", is_editable=False, is_default=False),
        "volume": schema_field("Volume", "integer", is_editable=False, is_default=False),
        "currency": schema_field("Currency", "string", is_editable=False, is_default=False),
    },

    "holding": {
        "quantity": schema_field(
            "Quantity", "decimal",
            is_editable=True, is_default=True,
            constraints={"decimal_places": 2},
            display_order=4,
        ),
        "purchase_price": schema_field(
            "Purchase Price", "decimal",
            is_editable=True, is_default=True,
            constraints={"decimal_places": 2},
            display_order=5,
        ),
        "purchase_date": schema_field(
            "Purchase Date", "date",
            is_editable=True, is_default=True,
            display_order=6,
        ),
    },

    "calculated": {
        "current_value_bond_fx": schema_field(
            "Current Value - Bond FX", "decimal",
            is_editable=False, is_default=True,
            formula_key="current_value_bond_fx",
            constraints={"decimal_places": 2, "min": Decimal("0")},
            display_order=7,
        ),
        "unrealized_gain": schema_field(
            "Unrealized Gain", "decimal",
            is_editable=False, is_default=False,
            formula_key="unrealized_gain",
            constraints={"decimal_places": 2},
        ),
    },
}
