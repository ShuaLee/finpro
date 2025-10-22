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
    MANAGED = "managed", "Managed Accounts"
    CUSTOM = "custom", "Custom"


DOMAIN_REGISTRY = {
    DomainType.EQUITY: {
        "label": "Equities",
        "schema_config": EQUITY_SCHEMA_CONFIG,
        "account_types": {
            "equity_self": {
                "label": "Brokerage Account",
                "description": (
                    "A self-directed brokerage account used to hold and trade equities, ETFs, "
                    "and other marketable securities such as bonds or precious metals."
                ),
            },
        },
        "allowed_assets": [DomainType.EQUITY],
    },
    DomainType.CRYPTO: {
        "label": "Cryptocurrency",
        "schema_config": CRYPTO_SCHEMA_CONFIG,
        "account_types": {
            "crypto_wallet": {
                "label": "Crypto Wallet",
                "description": (
                    "A digital wallet for storing and tracking cryptocurrency holdings, "
                    "including tokens and coins held on or off exchange."
                ),
            },
        },
        "allowed_assets": [DomainType.CRYPTO],
    },
    DomainType.METAL: {
        "label": "Metals",
        "schema_config": METAL_SCHEMA_CONFIG,
        "account_types": {
            "metal_storage": {
                "label": "Precious Metals Account",
                "description": (
                    "An account used to track physical or vaulted holdings of gold, silver, "
                    "and other precious metals."
                ),
            },
        },
        "allowed_assets": [DomainType.METAL],
    },
    DomainType.BOND: {
        "label": "Fixed Income",
        "schema_config": BOND_SCHEMA_CONFIG,
        "account_types": {
            "bond_broker": {
                "label": "Bond Brokerage Account",
                "description": (
                    "A self-directed account for trading or holding fixed income securities "
                    "such as government or corporate bonds."
                ),
            },
            "bond_trust": {
                "label": "Bond Trust Account",
                "description": (
                    "A trust or custodial account holding fixed income instruments managed "
                    "on behalf of a beneficiary."
                ),
            },
        },
        "allowed_assets": [DomainType.BOND],
    },
    DomainType.REAL_ESTATE: {
        "label": "Real Estate",
        "schema_config": REAL_ESTATE_SCHEMA_CONFIG,
        "account_types": {
            "real_estate": {
                "label": "Real Estate Holding",
                "description": (
                    "An account for tracking ownership and valuation of real estate assets, "
                    "including residential, commercial, or land holdings."
                ),
            },
        },
        "allowed_assets": [DomainType.REAL_ESTATE],
    },
    # DomainType.MANAGED: {
    #     "label": "Managed Accounts",
    #     "schema_config": MANAGED_SCHEMA_CONFIG,
    #     "account_types": {
    #         "managed_account": {
    #             "label": "Managed Portfolio",
    #             "description": (
    #                 "Represents a professionally managed investment portfolio "
    #                 "with defined allocations across asset classes (e.g., 80% equities, 20% bonds)."
    #             ),
    #         },
    #     },
    #     "allowed_assets": [],
    # },
    DomainType.CUSTOM: {
        "label": "Custom",
        "schema_config": CUSTOM_SCHEMA_CONFIG,
        "account_types": {
            "custom": {
                "label": "Custom Account",
                "description": (
                    "A flexible account type for tracking alternative or unsupported assets "
                    "with user-defined schema and attributes."
                ),
            },
        },
        "allowed_assets": [DomainType.CUSTOM],
    },
}

# ------------------------------------------------------
# 1️⃣ Domain & Account Lookup Helpers
# ------------------------------------------------------


def get_domain_for_account_type(account_type: str) -> str:
    """Return the domain type for a given account type."""
    for domain, meta in DOMAIN_REGISTRY.items():
        if account_type in meta.get("account_types", {}):
            return domain
    raise ValueError(f"Unknown account type: {account_type}")


def get_schema_config_for_account_type(account_type: str) -> dict:
    """Return the schema configuration for a given account type."""
    for meta in DOMAIN_REGISTRY.values():
        atypes = meta.get("account_types", {})
        if account_type in atypes:
            return atypes[account_type].get("schema_config", {})
    raise ValueError(
        f"No schema config found for account type: {account_type}")


def get_schema_config_for_domain(domain_type: str) -> dict:
    """
    Return the schema config for the *first* account type in a given domain.
    Useful when a domain has only one account type or uses a shared schema.
    """
    domain_meta = DOMAIN_REGISTRY.get(domain_type)
    if not domain_meta:
        raise ValueError(f"Unknown domain type: {domain_type}")

    account_types = list(domain_meta.get("account_types", {}).values())
    if not account_types:
        raise ValueError(
            f"No account types registered under domain '{domain_type}'.")

    # Return first schema_config found
    return account_types[0].get("schema_config", {})


def get_allowed_assets_for_domain(domain_type: str) -> list[str]:
    """Return allowed asset types for a given domain."""
    meta = DOMAIN_REGISTRY.get(domain_type)
    if not meta:
        raise ValueError(f"Unknown domain type: {domain_type}")
    return meta.get("allowed_assets", [])


# ------------------------------------------------------
# 2️⃣ Aggregated Metadata
# ------------------------------------------------------

def get_all_domain_types() -> list[str]:
    """Return all defined domain types (from DomainType)."""
    return [d.value for d in DomainType]


def get_all_account_types() -> list[str]:
    """Return a flat list of all registered account type keys."""
    return [
        atype
        for dmeta in DOMAIN_REGISTRY.values()
        for atype in dmeta.get("account_types", {}).keys()
    ]


def get_account_type_choices() -> list[tuple[str, str]]:
    """Return (value, label) pairs for Django field choices."""
    return [
        (atype, atmeta.get("label", atype.replace("_", " ").title()))
        for dmeta in DOMAIN_REGISTRY.values()
        for atype, atmeta in dmeta.get("account_types", {}).items()
    ]


def get_domain_meta(domain_type: str) -> dict:
    """
    Return full metadata for a given domain:
    includes allowed assets, account types, and their schema configs.
    """
    meta = DOMAIN_REGISTRY.get(domain_type)
    if not meta:
        raise ValueError(f"Unknown domain type: {domain_type}")

    account_types = meta.get("account_types", {})
    schema_configs = [
        a.get("schema_config", {}) for a in account_types.values()
    ]

    return {
        "domain": domain_type,
        "label": meta.get("label"),
        "allowed_assets": meta.get("allowed_assets", []),
        "account_types": list(account_types.keys()),
        "schema_configs": schema_configs,
        "schema_config": schema_configs[0] if schema_configs else None,
    }


# ------------------------------------------------------
# 3️⃣ Labels & UI Helpers
# ------------------------------------------------------

def get_label_for_domain(domain_type: str) -> str:
    """Return a human-readable label for a domain."""
    for choice in DomainType.choices:
        if choice[0] == domain_type:
            return choice[1]
    return domain_type.replace("_", " ").title()


def get_all_domains_with_labels() -> list[tuple[str, str]]:
    """Return all (domain, label) pairs for UI selection fields."""
    return [(d.value, d.label) for d in DomainType]


def get_all_schema_configs() -> dict[str, dict]:
    """Return a mapping of domain → representative schema config."""
    result = {}
    for domain in DOMAIN_REGISTRY.keys():
        try:
            result[domain] = get_schema_config_for_domain(domain)
        except ValueError:
            continue
    return result
