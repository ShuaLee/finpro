from schemas.config.utils import lookup_formula

EQUITY_TEMPLATE_CONFIG = {
    "account_type_slug": "brokerage",
    "name": "Equity Schema Template",
    "description": "Default schema template for equity portfolios.",

    "columns": [
        # ==========================================================
        # IDENTIFICATION FIELDS
        # ==========================================================
        {
            "title": "Symbol",
            "identifier": "symbol",
            "data_type": "string",
            "source": "asset",
            "source_field": "primary_identifier__value",
            "is_system": True,
            "is_editable": False,
            "is_deletable": False,
            "is_default": True,
            "display_order": 1,
            "constraints": {
                "max_length": 10,   # AAPL, MSFT, BRK.B etc.
            },
        },
        {
            "title": "Name",
            "identifier": "name",
            "data_type": "string",
            "source": "asset",
            "source_field": "name",
            "is_system": True,
            "is_editable": True,
            "is_deletable": False,
            "is_default": True,
            "display_order": 2,
            "constraints": {
                "max_length": 80,   # 'Berkshire Hathaway Class B'
            },
        },
        {
            "title": "Currency",
            "identifier": "currency",
            "data_type": "string",
            "source": "asset",
            "source_field": "currency",
            "is_system": True,
            "is_editable": True,
            "is_deletable": False,
            "is_default": True,
            "display_order": 3,
            "constraints": {
                "max_length": 50,   # USD, CAD, GBP...
            },
        },

        # ==========================================================
        # HOLDING FIELDS
        # ==========================================================
        {
            "title": "Purchase Price",
            "identifier": "purchase_price",
            "data_type": "decimal",
            "source": "holding",
            "source_field": "purchase_price",
            "is_system": True,
            "is_editable": True,
            "is_deletable": False,
            "is_default": True,
            "display_order": 4,
            "constraints": {
                "decimal_places": 2,   # USD prices → cents
                "min_value": 0,
                "max_value": None,
            },
        },
        {
            "title": "Quantity",
            "identifier": "quantity",
            "data_type": "decimal",
            "source": "holding",
            "source_field": "quantity",
            "is_system": True,
            "is_editable": True,
            "is_deletable": False,
            "is_default": True,
            "display_order": 5,
            "constraints": {
                # Equities support fractional shares (0.000001)
                "decimal_places": 6,
                "min_value": 0,
                "max_value": None,
            },
        },

        # ==========================================================
        # MARKET DATA FIELDS
        # ==========================================================
        {
            "title": "Last Price",
            "identifier": "last_price",
            "data_type": "decimal",
            "source": "asset",
            "source_field": "market_data__last_price",
            "is_system": True,
            "is_editable": True,
            "is_deletable": False,
            "is_default": True,
            "display_order": 6,
            "constraints": {
                "decimal_places": 2,
                "min_value": 0,
                "max_value": None,
            },
        },
        {
            "title": "Current Value - Asset FX",
            "identifier": "current_value_asset_fx",
            "data_type": "decimal",
            "source": "formula",
            "source_field": "current_value_asset_fx",
            "is_system": True,
            "is_editable": True,
            "is_deletable": False,
            "is_default": True,
            "display_order": 7,
            "constraints": {
                "decimal_places": 2,
            }
        },
        {
            "title": "Current Value - Profile FX",
            "identifier": "current_value_profile_fx",
            "data_type": "decimal",
            "source": "formula",
            "source_field": "current_value_profile_fx",
            "is_system": True,
            "is_editable": True,
            "is_deletable": False,
            "is_default": True,
            "display_order": 8,
            "constraints": {
                "decimal_places": 2,
            }
        },


        # ==========================================================
        # OPTIONAL MARKET DATA
        # ==========================================================
        {
            "title": "Market Cap",
            "identifier": "market_cap",
            "data_type": "integer",
            "source": "asset",
            "source_field": "market_data__market_cap",
            "is_system": True,
            "is_editable": True,
            "is_deletable": True,
            "is_default": False,
            "constraints": {
                "min_value": 0,
                "max_value": None,
            },
        },
        {
            "title": "P/E Ratio",
            "identifier": "pe_ratio",
            "data_type": "decimal",
            "source": "asset",
            "source_field": "market_data__pe_ratio",
            "is_system": True,
            "is_editable": True,
            "is_deletable": True,
            "is_default": False,
            "constraints": {
                "decimal_places": 2,  # Typical financial formatting
                "min_value": 0,
                "max_value": None,
            },
        },
        {
            "title": "EPS",
            "identifier": "eps",
            "data_type": "decimal",
            "source": "asset",
            "source_field": "market_data__eps",
            "is_system": True,
            "is_editable": True,
            "is_deletable": True,
            "is_default": False,
            "constraints": {
                "decimal_places": 2,  # EPS is money-like
                "min_value": None,    # EPS can be negative
                "max_value": None,
            },
        },
        {
            "title": "Dividend Yield",
            "identifier": "dividend_yield",
            "data_type": "decimal",
            "source": "asset",
            "source_field": "market_data__dividend_yield",
            "is_system": True,
            "is_editable": True,
            "is_deletable": True,
            "is_default": False,
            "constraints": {
                "decimal_places": 4,  # 3.5213% etc.
                "min_value": 0,
                "max_value": None,
            },
        },
        {
            "title": "Dividend Per Share",
            "identifier": "dividend_per_share",
            "data_type": "decimal",
            "source": "asset",
            "source_field": "market_data__dividend_per_share",
            "is_system": True,
            "is_editable": True,
            "is_deletable": True,
            "is_default": False,
            "constraints": {
                "decimal_places": 4,  # small dividend increments
                "min_value": 0,
                "max_value": None,
            },
        },
        {
            "title": "Purchase Date",
            "identifier": "purchase_date",
            "data_type": "date",
            "source": "holding",
            "source_field": "purchase_date",
            "is_system": True,
            "is_editable": True,
            "is_deletable": True,
            "is_default": False,
            "constraints": {},  # dates don’t use numeric constraints
        },
    ],
}
