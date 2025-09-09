from django.db import models

from accounts.models.account import Account
from accounts.models.details import (
    StockSelfManagedDetails,
    StockManagedDetails,
    CustomAccountDetails,
)

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
        "schema_config": STOCK_SCHEMA_CONFIG,
        "unique_subportfolio": True,
        "default_subportfolio_name": "Stock Portfolio",
        "account_details_models": [
            StockSelfManagedDetails,
            StockManagedDetails,
        ],
    },
    DomainType.CRYPTO: {
        "label": "Crypto",
        "schema_config": CRYPTO_SCHEMA_CONFIG,
        "unique_subportfolio": True,
        "default_subportfolio_name": "Crypto Portfolio",
        "account_details_models": [],
    },
    DomainType.METAL: {
        "label": "Metals",
        "schema_config": METAL_SCHEMA_CONFIG,
        "unique_subportfolio": True,
        "default_subportfolio_name": "Metal Portfolio",
        "account_details_models": [],
    },
    DomainType.CUSTOM: {
        "label": "Custom",
        "schema_config": CUSTOM_SCHEMA_CONFIG,
        "unique_subportfolio": False,
        "default_subportfolio_name": "Custom Portfolio",
        "account_details_models": [
            CustomAccountDetails,
        ],
    },
}


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


def get_all_domains_with_labels() -> list[tuple[str, str]]:
    return [(domain, meta["label"]) for domain, meta in DOMAIN_TYPE_REGISTRY.items()]


def get_account_details_models(domain_type: str) -> list[type[models.Model]]:
    return DOMAIN_TYPE_REGISTRY.get(domain_type, {}).get("account_details_models", [])


def get_account_detail_model_for(account: Account) -> type[models.Model] | None:
    """
    Given an account, return the matching details model class if it exists and is related.
    """
    for model in get_account_details_models(account.type):
        rel_name = model._meta.model_name
        if hasattr(account, rel_name):
            return model
    return None
