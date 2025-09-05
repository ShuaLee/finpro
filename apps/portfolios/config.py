from accounts.models.account import AccountType

SUBPORTFOLIO_CONFIG = {
    "stock": {
        "unique": True,
        "default_name": "Stock Portfolio",
        "schema_type": "stock",
        "account_types": [
            AccountType.STOCK_SELF_MANAGED,
            AccountType.STOCK_MANAGED,
        ],
    },
    "crypto": {
        "unique": True,
        "default_name": "Crypto Portfolio",
        "schema_type": "crypto",
        "account_types": [AccountType.CRYPTO_WALLET],
    },
    "metal": {
        "unique": True,
        "default_name": "Metal Portfolio",
        "schema_type": "metal",
        "account_types": [AccountType.METAL_STORAGE],
    },
    "custom": {
        "unique": False,
        "default_name": "Custom Portfolio",
        "schema_type": "custom",
        "account_types": [AccountType.CUSTOM],
    },
}
