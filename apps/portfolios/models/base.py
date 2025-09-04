"""
Base Model for Asset Portfolios
--------------------------------

This module defines `BaseAssetPortfolio`, an abstract base class for all asset-specific portfolios
(e.g., stocks, metals, crypto). It provides shared fields and behaviors common to all asset types.

Features:
- Common timestamp field (`created_at`).
- Can be extended by specific asset portfolio models for consistency.
"""
from django.contrib.contenttypes.models import ContentType
from django.db import models
from schemas.models.schema_link import SubPortfolioSchemaLink


class BaseAssetPortfolio(models.Model):
    """
    Abstract base model for all asset portfolios (Stocks, Metals, Crypto, etc.).

    Provides common fields such as creation timestamp.
    """
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def get_schema_for_account_model(self, account_model_or_key):
        """
        Resolve schema for the given account model type (or account_variant string).
        Centralized here so all derived portfolios (stock, crypto, metal, etc.) can use it.
        """
        # Allow passing either a model class or an account_variant string
        if isinstance(account_model_or_key, str):
            account_model = self._map_variant_to_model(account_model_or_key)
        else:
            account_model = account_model_or_key

        account_ct = ContentType.objects.get_for_model(account_model)

        link = SubPortfolioSchemaLink.objects.filter(
            subportfolio_ct=ContentType.objects.get_for_model(self.__class__),
            subportfolio_id=self.id,
            account_model_ct=account_ct,
        ).select_related("schema").first()

        return link.schema if link else None

    def _map_variant_to_model(self, variant: str):
        """
        Override this in subclasses if they have multiple account types.
        Example: StockPortfolio maps 'self_managed' -> SelfManagedAccount,
                 'managed' -> ManagedAccount.
        """
        raise NotImplementedError(
            "Portfolio subclass must implement account variant mapping")
