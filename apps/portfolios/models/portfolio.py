"""
Main Portfolio Model
--------------------

This module defines the `Portfolio` model, which represents a user's primary portfolio. 
It acts as the parent entity for multiple asset-specific portfolios (e.g., stocks, metals, crypto).

Responsibilities:
- Links to the user's `Profile` (one-to-one).
- Stores global settings like `profile_setup_complete`.
- Serves as the central entry point for managing all asset types.

Business Rules:
- One `Portfolio` per user profile.
"""

from django.db import models
from users.models import Profile


class Portfolio(models.Model):
    """
    Represents the main portfolio linked to a user's profile.

    Attributes:
        profile (OneToOneField): Each profile has one portfolio.
        created_at (DateTime): Timestamp when the portfolio is created.
        profile_setup_complete (bool): Indicates whether the portfolio is fully initialized.
    """

    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile} - {self.created_at}"

    def initialize_stock_portfolio(self):
        from apps.portfolios.models.stock import StockPortfolio
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

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.initialize_stock_portfolio()
