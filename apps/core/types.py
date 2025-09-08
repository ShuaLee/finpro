from django.db import models

# ✅ Import your actual schema config dicts
from schemas.config.stock import STOCK_SCHEMA_CONFIG
from schemas.config.crypto import CRYPTO_SCHEMA_CONFIG
from schemas.config.metal import METAL_SCHEMA_CONFIG
from schemas.config.custom_default import CUSTOM_SCHEMA_CONFIG

# 🔁 Optional: migrate AssetType/AccountType to pull from this registry later
from assets.models.asset import AssetType
from accounts.constants import AccountType


class DomainType(models.TextChoices):
    STOCK = "stock", "Stocks"
    CRYPTO = "crypto", "Crypto"
    METAL = "metal", "Metals"
    CUSTOM = "custom", "Custom"


# 🎯 Central registry for all schema + asset + account config by domain
DOMAIN_TYPE_REGISTRY = {
    DomainType.STOCK: {
        "label": "Stocks",
        "schema_config": STOCK_SCHEMA_CONFIG,
        "asset_type": AssetType.STOCK,
        "account_types": [
            AccountType.STOCK_SELF_MANAGED,
            AccountType.STOCK_MANAGED,
        ],
    },
    DomainType.CRYPTO: {
        "label": "Crypto",
        "schema_config": CRYPTO_SCHEMA_CONFIG,
        "asset_type": AssetType.CRYPTO,
        "account_types": [
            AccountType.CRYPTO_WALLET,
        ],
    },
    DomainType.METAL: {
        "label": "Metals",
        "schema_config": METAL_SCHEMA_CONFIG,
        "asset_type": AssetType.METAL,
        "account_types": [
            AccountType.METAL_STORAGE,
        ],
    },
    DomainType.CUSTOM: {
        "label": "Custom",
        "schema_config": CUSTOM_SCHEMA_CONFIG,
        "asset_type": AssetType.CUSTOM,
        "account_types": [
            AccountType.CUSTOM,
        ],
    },
}


def get_domain_type_from_account_type(account_type: str) -> str:
    for domain, meta in DOMAIN_TYPE_REGISTRY.items():
        if account_type in meta["account_types"]:
            return domain
    raise ValueError(f"Unknown account type: {account_type}")


def get_schema_config_for_account_type(account_type: str) -> dict:
    domain = get_domain_type_from_account_type(account_type)
    return DOMAIN_TYPE_REGISTRY[domain]["schema_config"]