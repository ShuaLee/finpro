SUBPORTFOLIO_CONFIG = {
    "stock": {
        "unique": True,
        "schema_type": "stock",
        "default_name": "Stock Portfolio",
    },
    "crypto": {
        "unique": True,
        "schema_type": "crypto",
        "default_name": "Crypto Portfolio",
    },
    "metal": {
        "unique": True,
        "schema_type": "metal",
        "default_name": "Precious Metal Portfolio",
    },
    "custom": {
        "unique": False,
        "schema_type": "custom",
        "default_name": "Custom Portfolio",
    },
}
