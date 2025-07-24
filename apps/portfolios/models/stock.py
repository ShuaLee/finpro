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
from .base import BaseAssetPortfolio


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


"""
    def initialize_stock_portfolio(self):
        from portfolios.models.stock import StockPortfolio
        from schemas.constants import DEFAULT_STOCK_SCHEMA_COLUMNS
        from schemas.models.stocks import StockPortfolioSchema, StockPortfolioSC

        if hasattr(self, 'stockportfolio'):
            return  # Already exists

        stock_portfolio = StockPortfolio.objects.create(portfolio=self)

        schema = StockPortfolioSchema.objects.create(
            stock_portfolio=stock_portfolio,
            name=f"Default Schema for {stock_portfolio}"
        )

        for column_data in DEFAULT_STOCK_SCHEMA_COLUMNS:
            StockPortfolioSC.objects.create(schema=schema, **column_data)
"""
