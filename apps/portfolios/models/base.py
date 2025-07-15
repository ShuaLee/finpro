"""
Base Model for Asset Portfolios
--------------------------------

This module defines `BaseAssetPortfolio`, an abstract base class for all asset-specific portfolios
(e.g., stocks, metals, crypto). It provides shared fields and behaviors common to all asset types.

Features:
- Common timestamp field (`created_at`).
- Can be extended by specific asset portfolio models for consistency.
"""

from django.db import models


class BaseAssetPortfolio(models.Model):
    """
    Abstract base model for all asset portfolios (Stocks, Metals, Crypto, etc.).

    Provides common fields such as creation timestamp.
    """
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
