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
from schemas.models import Schema
from decimal import Decimal


class StockPortfolio(BaseAssetPortfolio):
    """
    Represents a stock-specific portfolio under a main Portfolio.
    Tied to a single main Portfolio, with support for both self-managed
    and managed schemas.
    """
    portfolio = models.OneToOneField(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='stockportfolio'
    )

    self_managed_schema = models.ForeignKey(
        Schema, on_delete=models.PROTECT, related_name='stock_self_schema',
        null=True, blank=True
    )
    managed_schema = models.ForeignKey(
        Schema, on_delete=models.PROTECT, related_name='stock_managed_schema',
        null=True, blank=True
    )

    class Meta:
        app_label = 'portfolios'

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"

    def clean(self):
        # only enforce AFTER the row exists
        if self.pk and (not self.self_managed_schema_id or not self.managed_schema_id):
            raise ValidationError(
                "Both self-managed and managed schemas must be assigned.")

    def save(self, *args, **kwargs):
        # Allow the first insert without tripping the "schemas required" rule
        is_create = self.pk is None
        if not is_create:
            self.full_clean()
        super().save(*args, **kwargs)

    def get_total_value_pfx(self):
        """
        Returns total current value across all stock accounts in profile currency.
        Separates totals by mode for analysis.
        """
        from accounts.models import StockAccount  # delayed import to avoid circular

        self_accounts = StockAccount.objects.filter(
            stock_portfolio=self, account_mode="self_managed"
        ).select_related("stock_portfolio")

        managed_accounts = StockAccount.objects.filter(
            stock_portfolio=self, account_mode="managed"
        ).select_related("stock_portfolio")

        sm_total, sm_warnings = self._compute_account_total(
            self_accounts, mode="self_managed")
        m_total, m_warnings = self._compute_account_total(
            managed_accounts, mode="managed")

        return {
            "total": round(sm_total + m_total, 2),
            "self_total": sm_total,
            "managed_total": m_total,
            "warnings": sm_warnings + m_warnings
        }

    def _compute_account_total(self, accounts, mode):
        """
        Internal helper for computing total value for given accounts.
        """
        total = Decimal(0)
        warnings = []

        for acc in accounts:
            try:
                value = acc.get_current_value_in_pfx()
                if value is None:
                    raise ValueError("Returned None")
                total += value
            except Exception as e:
                warnings.append({
                    "account_id": acc.id,
                    "account_name": acc.name,
                    "type": mode,
                    "error": str(e)
                })

        return total, warnings
