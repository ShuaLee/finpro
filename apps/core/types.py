from django.db import models

from core.schema_config.stock import STOCK_SCHEMA_CONFIG
from core.schema_config.crypto import CRYPTO_SCHEMA_CONFIG
from core.schema_config.metal import METAL_SCHEMA_CONFIG
from core.schema_config.custom import CUSTOM_SCHEMA_CONFIG


class DomainType(models.TextChoices):
    STOCK = "stock", "Stocks"
    CRYPTO = "crypto", "Crypto"
    METAL = "metal", "Metals"
    CUSTOM = "custom", "Custom"


DOMAIN_TYPE_REGISTRY = {
    DomainType.STOCK: {
        "label": "Stocks",
        "unique_subportfolio": True,
        "default_subportfolio_name": "Stock Portfolio",
        "account_types": ["stock_self", "stock_managed"],
        "schema_config": STOCK_SCHEMA_CONFIG,
    },
    DomainType.CRYPTO: {
        "label": "Crypto",
        "unique_subportfolio": True,
        "default_subportfolio_name": "Crypto Portfolio",
        "account_types": ["crypto_wallet"],
        "schema_config": CRYPTO_SCHEMA_CONFIG,
    },
    DomainType.METAL: {
        "label": "Metals",
        "unique_subportfolio": True,
        "default_subportfolio_name": "Metal Portfolio",
        "account_types": ["metal_storage"],
        "schema_config": METAL_SCHEMA_CONFIG,
    },
    DomainType.CUSTOM: {
        "label": "Custom",
        "unique_subportfolio": False,
        "default_subportfolio_name": "Custom Portfolio",
        "account_types": ["custom"],
        "schema_config": CUSTOM_SCHEMA_CONFIG,
    },
}


# -------------------------------
# Core helpers
# -------------------------------
def get_schema_config_for_domain(domain_type: str) -> dict:
    if domain_type not in DOMAIN_TYPE_REGISTRY:
        raise ValueError(f"Unknown domain type: {domain_type}")
    return DOMAIN_TYPE_REGISTRY[domain_type]["schema_config"]


def get_label_for_domain(domain_type: str) -> str:
    return DOMAIN_TYPE_REGISTRY.get(domain_type, {}).get("label", domain_type.title())


def get_all_domain_types() -> list[str]:
    return list(DOMAIN_TYPE_REGISTRY.keys())


def get_all_schema_configs() -> dict[str, dict]:
    return {
        domain: meta["schema_config"]
        for domain, meta in DOMAIN_TYPE_REGISTRY.items()
    }


def get_domain_meta(domain_type: str) -> dict:
    """
    Return full domain metadata for a given domain type.
    Includes schema config, account types, and registry fields.
    """
    if domain_type not in DOMAIN_TYPE_REGISTRY:
        raise ValueError(f"Unknown domain type: {domain_type}")
    return DOMAIN_TYPE_REGISTRY[domain_type]


def get_all_domains_with_labels() -> list[tuple[str, str]]:
    return [(domain, meta["label"]) for domain, meta in DOMAIN_TYPE_REGISTRY.items()]


def get_domain_for_account_type(account_type: str) -> str:
    for domain, meta in DOMAIN_TYPE_REGISTRY.items():
        if account_type in meta.get("account_types", []):
            return domain
    raise ValueError(f"Unknown account type: {account_type}")


def get_account_type_choices() -> list[tuple[str, str]]:
    return [
        (atype, atype.replace("_", " ").title())
        for meta in DOMAIN_TYPE_REGISTRY.values()
        for atype in meta["account_types"]
    ]
