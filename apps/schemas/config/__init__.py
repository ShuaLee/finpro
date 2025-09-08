from accounts.models.account import AccountType
from schemas.config.stock import STOCK_SCHEMA_CONFIG
from schemas.config.crypto import CRYPTO_SCHEMA_CONFIG
from schemas.config.metal import METAL_SCHEMA_CONFIG
from schemas.config.custom_default import CUSTOM_SCHEMA_CONFIG

# Central registry mapping account types → schema config
SCHEMA_CONFIG_REGISTRY = {
    # Stocks
    AccountType.STOCK_SELF_MANAGED: STOCK_SCHEMA_CONFIG,
    AccountType.STOCK_MANAGED: STOCK_SCHEMA_CONFIG,

    # Crypto
    AccountType.CRYPTO_WALLET: CRYPTO_SCHEMA_CONFIG,

    # Metals
    AccountType.METAL_STORAGE: METAL_SCHEMA_CONFIG,

    # Custom
    AccountType.CUSTOM: CUSTOM_SCHEMA_CONFIG,
}
