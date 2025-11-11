CRYPTO_TEMPLATE_CONFIG = {
    "account_type": "crypto_wallet",
    "name": "Crypto Schema Template",
    "description": "Default schema template for crypto portfolios, covering tradable stock assets and holdings.",

    "columns": [
        # --- Identification (Default Columns) ---
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
        },
    ]
}
