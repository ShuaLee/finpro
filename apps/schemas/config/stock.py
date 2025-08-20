SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG = {
    "asset": {
        "ticker": {
            "title": "Ticker",
            "data_type": "string",
            "field_path": "stock.ticker",
            "editable": False,
            "is_deletable": False,
            "is_default": True,
            "is_system": True,
            "constraints": {},
        },
        "price": {
            "title": "Price",
            "data_type": "decimal",
            "field_path": "stock.price",
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
            "field_path": "stock.name",
            "editable": True,
            "is_deletable": True,
            "is_system": True,
            "constraints": {
                "character_limit": 200,
            },
        },
        "currency": {
            "title": "Currency",
            "data_type": "string",
            "field_path": "stock.currency",
            "editable": True,
            "is_deletable": True,
            "is_system": True,
            "constraints": {
                "character_limit": 3,
                "character_minimum": 3,
                "all_caps": True,
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
                "decimal_places": 4,
            },
        },
        "purchase_price": {
            "title": "Purchase Price",
            "data_type": "decimal",
            "field_path": "purchase_price",
            "editable": True,
            "is_deletable": True,
            "is_system": True,
            "constraints": {
                "decimal_places": 2,
                "min": 0,
            },
        },
    },
    "calculated": {
        "current_value_stock_fx": {
            "title": "Current Value - Stock FX",
            "data_type": "decimal",
            "formula_method": "current_value_stock_fx",
            "editable": False,
            "is_deletable": False,
            "is_default": True,
            "is_system": True,
            "constraints": {
                "decimal_places": 2,
                "min": 0,
            },
        },
        "current_value_profile_fx": {
            "title": "Current Value - Profile FX",
            "data_type": "decimal",
            "formula_method": "current_value_profile_fx",
            "editable": False,
            "is_deletable": False,
            "is_default": True,
            "is_system": True,
            "constraints": {
                "decimal_places": 2,
                "min": 0,
            },
        },
        "unrealized_gain": {
            "title": "Unrealized Gain",
            "data_type": "decimal",
            "formula_method": "get_unrealized_gain",
            "editable": False,
            "is_deletable": True,
            "is_system": True,
            "constraints": {
                "decimal_places": 2,
                "min": 0,
            },
        },
    },
}

MANAGED_ACCOUNT_SCHEMA_CONFIG = {
    "custom": {
        "title": {
            "title": "Title",
            "data_type": "string",
            "editable": True,
            "is_deletable": False,
            "is_default": True,
            "is_system": True,
            "constraints": {
                "character_limit": 200,
                "character_minimum": 0,
            },

        },
        "current_value": {
            "title": "Current Value",
            "data_type": "decimal",
            "editable": False,
            "is_deletable": False,
            "is_default": True,
            "is_system": True,
            "constraints": {
                "decimal_places": 2,
                "min": 0,
            },
        },
        "currency": {
            "title": "Currency",
            "data_type": "string",
            "editable": False,
            "is_deletable": False,
            "is_default": True,
            "is_system": True,
            "constraints": {
                "character_limit": 3,
                "character_minimum": 3,
                "all_caps": True,
            },
        },
    },
}
