from accounts.models.crypto import CryptoWallet
from accounts.models.custom import CustomAccount
from accounts.models.metals import StorageFacility
from accounts.models.stocks import SelfManagedAccount, ManagedAccount
from schemas.config.schema_registry.stock import SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG, MANAGED_ACCOUNT_SCHEMA_CONFIG
from schemas.config.schema_registry.crypto import CRYPTO_WALLET_SCHEMA_CONFIG
from schemas.config.schema_registry.custom_default import CUSTOM_DEFAULT_SCHEMA_CONFIG
from schemas.config.schema_registry.metal import METALS_STORAGE_FACILITY_SCHEMA_CONFIG
# from .custom import DEFAULT_COLUMNS as CUSTOM_DEFAULT_COLUMNS

SCHEMA_CONFIG_REGISTRY = {
    "stock": {
        ManagedAccount: MANAGED_ACCOUNT_SCHEMA_CONFIG,
        SelfManagedAccount: SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG,
    },
    "crypto": {
        CryptoWallet: CRYPTO_WALLET_SCHEMA_CONFIG,
    },
    "custom_default": {
        CustomAccount: CUSTOM_DEFAULT_SCHEMA_CONFIG,
    },
    "metal": {
        StorageFacility: METALS_STORAGE_FACILITY_SCHEMA_CONFIG,
    },
    # "custom": { ... }
}
