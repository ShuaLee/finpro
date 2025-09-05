from accounts.models.account import AccountType, Account
from schemas.config.schema_registry.stock import (
    SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG,
    MANAGED_ACCOUNT_SCHEMA_CONFIG,
)
from schemas.config.schema_registry.crypto import CRYPTO_ACCOUNT_SCHEMA_CONFIG
from schemas.config.schema_registry.custom_default import CUSTOM_ACCOUNT_SCHEMA_CONFIG
from schemas.config.schema_registry.metal import METALS_ACCOUNT_SCHEMA_CONFIG


# Registry now keyed by AccountType values instead of model classes
SCHEMA_CONFIG_REGISTRY = {
    AccountType.STOCK_SELF_MANAGED: SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG,
    AccountType.STOCK_MANAGED: MANAGED_ACCOUNT_SCHEMA_CONFIG,
    AccountType.CRYPTO_WALLET: CRYPTO_ACCOUNT_SCHEMA_CONFIG,
    AccountType.METAL_STORAGE: METALS_ACCOUNT_SCHEMA_CONFIG,
    AccountType.CUSTOM: CUSTOM_ACCOUNT_SCHEMA_CONFIG,
}
