"""
Metal Portfolio Model
----------------------

This module defines the `MetalPortfolio` model, which represents a metals-specific portfolio 
associated with a user's main portfolio.

Responsibilities:
- One-to-one relationship with `Portfolio`.
- Enforces uniqueness and schema presence.
- Serves as a container for metals-related holdings and data.

Business Rules:
- Only one MetalPortfolio is allowed per Portfolio.
- Must have at least one schema (enforced by `clean()`).
"""
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from schemas.models.schema_link import SubPortfolioSchemaLink
from portfolios.models.portfolio import Portfolio
from .base import BaseAssetPortfolio


class MetalPortfolio(BaseAssetPortfolio):
    """
    Represents a metal-specific portfolio under a main Portfolio.
    """
    portfolio = models.OneToOneField(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='metalportfolio'
    )

    class Meta:
        app_label = 'portfolios'

    def __str__(self):
        return f"Metal Portfolio for {self.portfolio.profile.user.email}"
    
    def clean(self):
        if self.pk is None and MetalPortfolio.objects.filter(portfolio=self.portfolio).exists():
            raise ValidationError("Only one MetalPortfolio is allowed per Portfolio.")

        if self.pk and not self.schemas.exists():
            raise ValidationError("MetalPortfolio must have at least one schema.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

