from .stock import STOCK_SCHEMA_CONFIG, STOCK_MANAGED_SCHEMA_CONFIG
# from .metal import DEFAULT_COLUMNS as METAL_DEFAULT_COLUMNS
# from .custom import DEFAULT_COLUMNS as CUSTOM_DEFAULT_COLUMNS

SCHEMA_CONFIG_REGISTRY = {
    "stock": {
        "managed": STOCK_MANAGED_SCHEMA_CONFIG,
        "self_managed": STOCK_SCHEMA_CONFIG,
    },
    # "precious_metal": { ... },
    # "custom": { ... }
}