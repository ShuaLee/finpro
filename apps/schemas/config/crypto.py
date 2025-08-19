CRYPTO_SCHEMA_CONFIG = {
    "asset": {
        "ticker": {
            "title": "Ticker",
            "data_type": "string",
            "field_path": "crypto.ticker",
            "editable": False,
            "is_deletable": False,
            "is_system": True,
            "constraints": {
                "character_limit": 10
            }
        },
        "price": {
            "title": "Price",
            "data_type": "decimal",
            "field_path": "crypto.price",
            "editable": True,
            "is_deletable": False,
            "is_default": True,
            "is_system": True,
            "constraints": {
                "decimal_places": 2,
                "min": 0,
            }
        },
        "name": {
            "title": "Name",
            "data_type": "string",
            "field_path": "crypto.name",
            "editable": True,
            "is_deletable": True,
            "is_default": True,
            "is_system": True,
            "constraints": {
                "character_limit": 200,
            },
        },
    },
    "holding": {
        "quantity": {
            "title": "Quantity",
            "data_type": "decimal",
            "field_path": "quantity",
            "editable": True,
            "is_deletable": False,
            "is_default": True,
            "is_system": True,
            "constraints": {
                "decimal_places": 8,
                "min": 0
            },
        },
    }
}