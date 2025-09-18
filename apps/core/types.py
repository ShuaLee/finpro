from django.db import models

from core.schema_config.equity import EQUITY_SCHEMA_CONFIG
from core.schema_config.crypto import CRYPTO_SCHEMA_CONFIG
from core.schema_config.metal import METAL_SCHEMA_CONFIG
from core.schema_config.bond import BOND_SCHEMA_CONFIG
from core.schema_config.real_estate import REAL_ESTATE_SCHEMA_CONFIG
from core.schema_config.custom import CUSTOM_SCHEMA_CONFIG


class DomainType(models.TextChoices):
    EQUITY = "equity", "Equities"
    CRYPTO = "crypto", "Crypto"
    METAL = "metal", "Metals"
    BOND = "bond", "Bonds"
    REAL_ESTATE = "real_estate", "Real Estate"
    CUSTOM = "custom", "Custom"


DOMAIN_TYPE_REGISTRY = {
    DomainType.EQUITY: {
        "label": "Equities",
        "account_types": ["equity_self", "equity_managed"],
        "allowed_assets": [DomainType.EQUITY, DomainType.BOND],
        "schema_config": EQUITY_SCHEMA_CONFIG,
    },
    DomainType.CRYPTO: {
        "label": "Crypto",
        "account_types": ["crypto_wallet"],
        "allowed_assets": [DomainType.CRYPTO],
        "schema_config": CRYPTO_SCHEMA_CONFIG,
    },
    DomainType.METAL: {
        "label": "Metals",
        "account_types": ["metal_storage"],
        "allowed_assets": [DomainType.METAL],
        "schema_config": METAL_SCHEMA_CONFIG,
    },
    DomainType.BOND: {
        "label": "Bonds",
        "account_types": ["bond_broker", "bond_trust"],
        "allowed_assets": [DomainType.BOND],
        "schema_config": BOND_SCHEMA_CONFIG,
    },
    DomainType.REAL_ESTATE: {
        "label": "Real Estate",
        "account_types": ["real_estate"],
        "allowed_assets": [DomainType.REAL_ESTATE],
        "schema_config": REAL_ESTATE_SCHEMA_CONFIG,
    },
    DomainType.CUSTOM: {
        "label": "Custom",
        "account_types": ["custom"],
        "allowed_assets": [DomainType.CUSTOM],
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
