CRYPTO_TEMPLATE_CONFIG = {
    "account_type_slug": "crypto_wallet",
    "name": "Crypto Schema Template",
    "description": "Default schema template for crypto portfolios.",

    "columns": [
        # --- Default Columns ---
        {
            "title": "Symbol",
            "identifier": "symbol",
            "data_type": "string",
            "source": "asset",
            "source_field": "crypto_detail__base_symbol",
            "is_system": True,
            "is_editable": False,
            "is_deletable": False,
            "is_default": True,
            "display_order": 1,
            "constraints": {
                "max_length": 20,
            }
        },
        {
            "title": "Name",
            "identifier": "name",
            "data_type": "string",
            "source": "asset",
            "source_field": "name",
            "is_system": True,
            "is_editable": False,
            "is_deletable": False,
            "is_default": True,
            "display_order": 2,
            "constraints": {
                "max_length": 20,
            }
        },
        {
            "title": "Currency",
            "identifier": "currency",
            "data_type": "string",
            "source": "asset",
            "source_field": "currency",
            "is_system": True,
            "is_editable": False,
            "is_deletable": False,
            "is_default": True,
            "display_order": 3,
            "constraints": {
                "max_length": 50,
            },
        },

        # --- Holding ---
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
            # Crypto prices can be tiny (many zeros)
            # 8 decimals matches Bitcoin price precision (0.00000001)
            "constraints": {
                "decimal_places": 2,
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
            # Most crypto assets support up to 18 decimals (ERC20 standard)
            "constraints": {
                "decimal_places": 18,
                "min_value": 0,
                "max_value": None,
            },
        },

        # --- Market Data ---
        {
            "title": "Last Price",
            "identifier": "last_price",
            "data_type": "decimal",
            "source": "asset",
            "source_field": "market_data__last_price",
            "is_system": True,
            "is_editable": False,
            "is_deletable": False,
            "is_default": True,
            "display_order": 6,
            # FMP crypto prices are normally 8 decimals max
            "constraints": {
                "decimal_places": 2,
                "min_value": 0,
                "max_value": None,
            },
        },
        {
            "title": "Market Cap",
            "identifier": "market_cap",
            "data_type": "integer",
            "source": "asset",
            "source_field": "market_data__market_cap",
            "is_system": True,
            "is_editable": False,
            "is_deletable": True,
            "is_default": False,
            "constraints": {
                "min_value": 0,
                "max_value": None,
            },
        },

        # --- Optional: Pair Symbol ---
        {
            "title": "Pair Symbol",
            "identifier": "pair_symbol",
            "data_type": "string",
            "source": "asset",
            "source_field": "crypto_detail__pair_symbol",
            "is_system": True,
            "is_editable": False,
            "is_deletable": True,
            "is_default": False,
            "constraints": {
                "max_length": 20,
            },
        },

        # --- Formulas ---
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
    ],
}
