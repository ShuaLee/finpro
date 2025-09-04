"""
Stock Portfolio Model
----------------------

This module defines the `StockPortfolio` model, representing a stock-specific portfolio tied 
to a user's main portfolio.

Responsibilities:
- One-to-one relationship with `Portfolio`.
- Enforces validation for uniqueness and schema existence.
- Provides stock-specific features in the future (e.g., stock positions, performance metrics).

Business Rules:
- Only one StockPortfolio is allowed per Portfolio.
- Must have at least one schema (enforced by `clean()`).
"""

from django.core.exceptions import ValidationError
from django.db import models
from portfolios.models.portfolio import Portfolio
from portfolios.models.base import BaseAssetPortfolio
from decimal import Decimal


class StockPortfolio(BaseAssetPortfolio):
    """
    Represents a stock-specific portfolio under a main Portfolio.

    Attributes:
        portfolio (OneToOneField): Links to the main Portfolio.
    """
    portfolio = models.OneToOneField(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='stockportfolio'
    )

    class Meta:
        app_label = 'portfolios'

    def _map_variant_to_model(self, variant: str):
        from accounts.models.stocks import SelfManagedAccount, ManagedAccount
        if variant == "self_managed":
            return SelfManagedAccount
        elif variant == "managed":
            return ManagedAccount
        raise ValueError(f"Unknown account variant: {variant}")

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"

    def clean(self):
        """
        Validates that only one StockPortfolio exists per Portfolio
        and ensures schemas exist when updating.
        """
        if self.pk is None and StockPortfolio.objects.filter(portfolio=self.portfolio).exists():
            raise ValidationError(
                "Only one StockPortfolio is allowed per Portfolio.")

        if self.pk and not self.schemas.exists():
            raise ValidationError(
                "StockPortfolio must have at least one schema.")

    def save(self, *args, **kwargs):
        """
        Override save to ensure model validation before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def get_self_managed_total_pfx(self):
        from accounts.models import SelfManagedAccount

        total = Decimal(0)
        warnings = []

        for acc in SelfManagedAccount.objects.filter(stock_portfolio=self):
            try:
                value = acc.get_current_value_pfx()
                if value is None:
                    raise ValueError("Returned None")
                total += Decimal(value)
            except Exception as e:
                warnings.append({
                    "account_id": acc.id,
                    "account_name": acc.name,
                    "type": "self_managed",
                    "error": str(e)
                })

        return total, warnings

    def get_managed_total_pfx(self):
        from accounts.models import ManagedAccount

        total = Decimal(0)
        warnings = []

        for acc in ManagedAccount.objects.filter(stock_portfolio=self):
            try:
                value = acc.get_current_value_in_profile_fx()
                if value is None:
                    raise ValueError("Returned None")
                total += Decimal(value)
            except Exception as e:
                warnings.append({
                    "account_id": acc.id,
                    "account_name": acc.name,
                    "type": "managed",
                    "error": str(e)
                })

        return total, warnings

    def get_total_value_pfx(self):
        sm_total, sm_warnings = self.get_self_managed_total_pfx()
        m_total, m_warnings = self.get_managed_total_pfx()
        return {
            "total": round(sm_total + m_total, 2),
            "self_total": sm_total,
            "managed_total": m_total,
            "warnings": sm_warnings + m_warnings
        }
