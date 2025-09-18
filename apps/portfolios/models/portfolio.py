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

    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='portfolio'
    )
    name = models.CharField(max_length=100, default="Main Portfolio")
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile"],
                condition=models.Q(is_main=True),
                name="unique_main_portfolio_per_profile",
            ),
            models.UniqueConstraint(
                fields=["profile", "name"],
                name="unique_portfolio_name_prt_profile",
            )
        ]

    def __str__(self):
        return f"{self.profile.user.email} - {self.name}"
