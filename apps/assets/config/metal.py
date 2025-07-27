METAL_SCHEMA_CONFIG = {
    "asset": {
        "name": {
            "data_type": "string",
            "editable": False,
            "field_path": "holding.preciousmetal.name",
        },
        "price": {
            "data_type": "decimal",
            "editable": True,
            "field_path": "holding.preciousmetal.price",
        },
    },
    "holding": {
        "quantity": {
            "data_type": "decimal",
            "editable": True,
            "field_path": "holding.quantity",
            "decimal_spaces": 4,
        },
        "purchase_price": {
            "data_type": "decimal",
            "editable": True,
            "field_path": "holding.purchase_price",
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
    },
}
