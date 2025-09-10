from typing import Type
from django.db import models

from core.types import DOMAIN_TYPE_REGISTRY, DomainType
from accounts.models.details import (
    StockSelfManagedDetails,
    StockManagedDetails,
    CustomAccountDetails,
)


ACCOUNT_DETAILS_MODELS = {
    DomainType.STOCK: [StockSelfManagedDetails, StockManagedDetails],
    DomainType.CRYPTO: [],
    DomainType.METAL: [],
    DomainType.CUSTOM: [CustomAccountDetails],
}


def get_account_details_models(domain_type: str) -> list[Type[models.Model]]:
    """Return all eligible detail models for a given domain type."""
    return ACCOUNT_DETAILS_MODELS.get(domain_type, [])


def get_account_detail_model_for(account) -> Type[models.Model] | None:
    # ✅ move here to avoid circular import
    from accounts.models.account import Account

    for model in get_account_details_models(account.domain_type):
        rel_name = model._meta.model_name
        if hasattr(account, rel_name):
            return model
    return None


def get_domain_meta_with_details(domain_type: str) -> dict:
    """Return full domain metadata, enriched with account detail models."""
    if domain_type not in DOMAIN_TYPE_REGISTRY:
        raise ValueError(f"Unknown domain type: {domain_type}")

    base = DOMAIN_TYPE_REGISTRY[domain_type]
    return {**base, "account_details_models": get_account_details_models(domain_type)}
