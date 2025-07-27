from .stock import STOCK_SCHEMA_CONFIG
from .metal import METAL_SCHEMA_CONFIG

ASSET_SCHEMA_CONFIG = {
    "stock": STOCK_SCHEMA_CONFIG,
    "precious_metal": METAL_SCHEMA_CONFIG,
    # future: add crypto, real estate, etc.
}
