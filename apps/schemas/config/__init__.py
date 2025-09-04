from accounts.models.crypto import CryptoAccount
from accounts.models.custom import CustomAccount
from accounts.models.metals import MetalAccount
from accounts.models.stocks import SelfManagedAccount, ManagedAccount
from schemas.config.schema_registry.stock import SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG, MANAGED_ACCOUNT_SCHEMA_CONFIG
from schemas.config.schema_registry.crypto import CRYPTO_ACCOUNT_SCHEMA_CONFIG
from schemas.config.schema_registry.custom_default import CUSTOM_ACCOUNT_SCHEMA_CONFIG
from schemas.config.schema_registry.metal import METALS_ACCOUNT_SCHEMA_CONFIG
# from .custom import DEFAULT_COLUMNS as CUSTOM_DEFAULT_COLUMNS

SCHEMA_CONFIG_REGISTRY = {
    "stock": {
        ManagedAccount: MANAGED_ACCOUNT_SCHEMA_CONFIG,
        SelfManagedAccount: SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG,
    },
    "crypto": {
        CryptoAccount: CRYPTO_ACCOUNT_SCHEMA_CONFIG,
    },
    "custom_default": {
        CustomAccount: CUSTOM_ACCOUNT_SCHEMA_CONFIG,
    },
    "metal": {
        MetalAccount: METALS_ACCOUNT_SCHEMA_CONFIG,
    },
    # "custom": { ... }
}
