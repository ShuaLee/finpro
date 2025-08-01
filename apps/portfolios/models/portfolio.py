"""
Main Portfolio Model
--------------------

Represents the `Portfolio` model, which is the primary container for all of a user's investments.
Acts as the parent entity for multiple asset-specific portfolios (e.g., stocks, metals, crypto).

Responsibilities:
- Links to the user's `Profile` (one-to-one).
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
    """

    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'portfolios'

    def __str__(self):
        return f"{self.profile} - {self.created_at}"

    def get_total_value_pfx(self):
        """
        Should be implemented by subclass (e.g. StockPortfolio, MetalPortfolio)
        """
        raise NotImplementedError(
            "Subclasses must implement get_total_value()")
