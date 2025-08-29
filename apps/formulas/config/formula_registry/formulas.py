FORMULAS_REGISTRY = {
    "current_value_stock_fx": {
        "title": "Current Value - Stock FX",
        "expression": "quantity * price",
        "dependencies": ["quantity", "price"],
        "decimal_places": 2,
        "is_system": True,
    },
    "current_value_profile_fx": {
        "title": "Current Value - Profile FX",
        "expression": "(quantity * price) * fx_rate",
        "dependencies": ["quantity", "price", "fx_rate"],
        "decimal_places": 2,
        "is_system": True,
    },
    "unrealized_gain": {
        "title": "Unrealized Gain",
        "expression": "(price - purchase_price) * quantity",
        "dependencies": ["price", "purchase_price", "quantity"],
        "decimal_places": 2,
        "is_system": True,
    },
}
