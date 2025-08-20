from accounts.models.stocks import SelfManagedAccount, ManagedAccount
from accounts.models.crypto import CryptoWallet
from accounts.models.custom import CustomAccount
from .stock import SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG, MANAGED_ACCOUNT_SCHEMA_CONFIG
from .crypto import CRYPTO_WALLET_SCHEMA_CONFIG
from .custom_default import CUSTOM_DEFAULT_SCHEMA_CONFIG
# from .metal import DEFAULT_COLUMNS as METAL_DEFAULT_COLUMNS
# from .custom import DEFAULT_COLUMNS as CUSTOM_DEFAULT_COLUMNS

SCHEMA_CONFIG_REGISTRY = {
    "stock": {
        ManagedAccount: SELF_MANAGED_ACCOUNT_SCHEMA_CONFIG,
        SelfManagedAccount: MANAGED_ACCOUNT_SCHEMA_CONFIG,
    },
    "crypto": {
        CryptoWallet: CRYPTO_WALLET_SCHEMA_CONFIG,
    },
    "custom_default": {                       
        CustomAccount: CUSTOM_DEFAULT_SCHEMA_CONFIG,
    },
    # "precious_metal": { ... },
    # "custom": { ... }
}
