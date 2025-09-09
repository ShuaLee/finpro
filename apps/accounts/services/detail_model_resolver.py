from typing import Type
from django.db import models

from core.types import DomainType
from accounts.models.account import Account
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
    """
    Return all eligible detail models for a given domain type.
    """
    return ACCOUNT_DETAILS_MODELS.get(domain_type, [])


def get_account_detail_model_for(account: Account) -> Type[models.Model] | None:
    """
    Given an Account instance, return the detail model class if one exists and is related.
    """
    for model in get_account_details_models(account.type):
        rel_name = model._meta.model_name
        if hasattr(account, rel_name):
            return model
    return None
