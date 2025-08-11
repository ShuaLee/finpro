STOCK_SCHEMA_CONFIG = {
    "asset": {
        "ticker": {
            "title": "Ticker",
            "data_type": "string",
            "field_path": "stock.ticker",
            "editable": False,
            "is_deletable": False,
            "is_default": True,
        },
        "price": {
            "title": "Price",
            "data_type": "decimal",
            "field_path": "stock.price",
            "editable": False,
            "decimal_places": 2,
            "is_deletable": False,
            "is_default": True,
        },
        "name": {
            "title": "Name",
            "data_type": "string",
            "field_path": "stock.name",
            "editable": True,
            "is_deletable": True,
        },
    },
    "holding": {
        "quantity": {
            "title": "Quantity",
            "data_type": "decimal",
            "field_path": "quantity",
            "editable": True,
            "decimal_places": 4,
            "is_deletable": False,
            "is_default": True,
        },
        "purchase_price": {
            "title": "Purchase Price",
            "data_type": "decimal",
            "field_path": "purchase_price",
            "editable": True,
            "decimal_places": 2,
            "is_deletable": True,
        },
    },
    "calculated": {
        "current_value": {
            "title": "Current Value",
            "data_type": "decimal",
            "editable": False,
            "decimal_places": 2,
            "is_deletable": False,
            "is_default": True,
        },
        "unrealized_gain": {
            "title": "Unrealized Gain",
            "data_type": "decimal",
            "formula_method": "get_unrealized_gain",
            "editable": False,
            "decimal_places": 2,
        },
    },
}

STOCK_MANAGED_SCHEMA_CONFIG = {
    "custom": {
        "current_value": {
            "title": "Current Value",
            "data_type": "decimal",
            "editable": False,
            "decimal_places": 2,
            "is_deletable": False,
            "is_default": True,
        },
        "currency": {
            "title": "Currency",
            "data_type": "string",
            "editable": False,
            "is_deletable": False,
            "is_default": True,
        },
    },
}
