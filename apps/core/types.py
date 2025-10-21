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


ACCOUNT_TYPE_REGISTRY = {
    "equity_self": {
        "domain": DomainType.EQUITY,
        "schema_config": EQUITY_SCHEMA_CONFIG,
        "allowed_assets": [DomainType.EQUITY],
    },
    "equity_managed": {
        "domain": DomainType.EQUITY,
        "schema_config": EQUITY_SCHEMA_CONFIG,
        "allowed_assets": [DomainType.EQUITY],
    },
    "crypto_wallet": {
        "domain": DomainType.CRYPTO,
        "schema_config": CRYPTO_SCHEMA_CONFIG,
        "allowed_assets": [DomainType.CRYPTO],
    },
    "metal_storage": {
        "domain": DomainType.METAL,
        "schema_config": METAL_SCHEMA_CONFIG,
        "allowed_assets": [DomainType.METAL],
    },
    "bond_broker": {
        "domain": DomainType.BOND,
        "schema_config": BOND_SCHEMA_CONFIG,
        "allowed_assets": [DomainType.BOND],
    },
    "bond_trust": {
        "domain": DomainType.BOND,
        "schema_config": BOND_SCHEMA_CONFIG,
        "allowed_assets": [DomainType.BOND],
    },
    "real_estate": {
        "domain": DomainType.REAL_ESTATE,
        "schema_config": REAL_ESTATE_SCHEMA_CONFIG,
        "allowed_assets": [DomainType.REAL_ESTATE],
    },
    "custom": {
        "domain": DomainType.CUSTOM,
        "schema_config": CUSTOM_SCHEMA_CONFIG,
        "allowed_assets": [DomainType.CUSTOM],
    },
}


def get_domain_for_account_type(account_type: str) -> str:
    """Return the domain type for a given account type."""
    if account_type not in ACCOUNT_TYPE_REGISTRY:
        raise ValueError(f"Unknown account type: {account_type}")
    return ACCOUNT_TYPE_REGISTRY[account_type]["domain"]


def get_schema_config_for_account_type(account_type: str) -> dict:
    """Return schema config for a given account type."""
    if account_type not in ACCOUNT_TYPE_REGISTRY:
        raise ValueError(f"Unknown account type: {account_type}")
    return ACCOUNT_TYPE_REGISTRY[account_type]["schema_config"]


def get_schema_config_for_domain(domain_type: str) -> dict:
    """
    Return the schema config for the *first* account type in a given domain.
    Used when schema config is domain-wide (same for all account types in that domain).
    """
    for cfg in ACCOUNT_TYPE_REGISTRY.values():
        if cfg["domain"] == domain_type:
            return cfg["schema_config"]
    raise ValueError(f"No schema config found for domain: {domain_type}")


def get_allowed_assets_for_domain(domain_type: str) -> list[str]:
    """Aggregate allowed asset types across all account types in the domain."""
    allowed = set()
    for cfg in ACCOUNT_TYPE_REGISTRY.values():
        if cfg["domain"] == domain_type:
            allowed.update(cfg.get("allowed_assets", []))
    return list(allowed)


def get_all_domain_types() -> list[str]:
    """Return a list of all distinct domain types (from DomainType enum)."""
    return [choice.value for choice in DomainType]


def get_all_account_types() -> list[str]:
    """Return all registered account types."""
    return list(ACCOUNT_TYPE_REGISTRY.keys())


def get_account_type_choices() -> list[tuple[str, str]]:
    """Return account type choices for Django field usage."""
    return [
        (atype, atype.replace("_", " ").title())
        for atype in ACCOUNT_TYPE_REGISTRY.keys()
    ]


def get_domain_meta(domain_type: str) -> dict:
    """
    Return full domain metadata composed from all account types in that domain.
    Includes aggregated allowed assets and schema configs.
    """
    metas = [cfg for cfg in ACCOUNT_TYPE_REGISTRY.values() if cfg["domain"]
             == domain_type]
    if not metas:
        raise ValueError(f"Unknown domain type: {domain_type}")

    allowed_assets = set()
    schema_configs = []
    for m in metas:
        allowed_assets.update(m.get("allowed_assets", []))
        schema_configs.append(m.get("schema_config", {}))

    return {
        "domain": domain_type,
        "allowed_assets": list(allowed_assets),
        "schema_configs": schema_configs,
        "account_types": [k for k, v in ACCOUNT_TYPE_REGISTRY.items() if v["domain"] == domain_type],
    }


def get_label_for_domain(domain_type: str) -> str:
    """Return a human-readable label for a domain."""
    for choice in DomainType.choices:
        if choice[0] == domain_type:
            return choice[1]
    return domain_type.title()


def get_all_domains_with_labels() -> list[tuple[str, str]]:
    """Return list of (domain_type, label) pairs for UI or field choices."""
    return [(d.value, d.label) for d in DomainType]


def get_all_schema_configs() -> dict[str, dict]:
    """Return a mapping of domain → representative schema config."""
    result = {}
    for domain in get_all_domain_types():
        try:
            result[domain] = get_schema_config_for_domain(domain)
        except ValueError:
            continue
    return result
