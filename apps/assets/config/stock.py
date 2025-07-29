STOCK_SCHEMA_CONFIG = {
    "asset": {
        "ticker": {
            "data_type": "string",
            "editable": False,
            "field_path": "stock.ticker",
            "api_field": "symbol",
            "source": "quote",
        },
        "price": {
            "data_type": "decimal",
            "editable": True,
            "field_path": "stock.price",
            "decimal_spaces": 2,
            "api_field": "price",
            "source": "quote",
        },
        "name": {
            "data_type": "string",
            "editable": True,
            "field_path": "stock.name",
            "api_field": "name",
            "source": "profile",
        },
    },
    "holding": {
        "quantity": {
            "data_type": "decimal",
            "editable": True,
            "field_path": "quantity",
            "decimal_spaces": 4,
        },
        "purchase_price": {
            "data_type": "decimal",
            "editable": True,
            "field_path": "purchase_price",
            "decimal_spaces": 2,
        },
    },
    "calculated": {
        "current_value": {
            "data_type": "decimal",
            "editable": False,
            "formula_required": False,
            "formula_method": "get_current_value",
        },
        "unrealized_gain": {
            "data_type": "decimal",
            "editable": False,
            "formula_required": True,
            "formula_method": "get_unrealized_gain",
        },
    },
}
