from django.db import models
from django.utils.text import slugify


class Plan(models.Model):
    """
    Represents a subscription plan for the investment tracking platform.

    Each plan determines what features a user has access to,
    such as the number of stocks allowed, whether crypto and metals
    tracking is available, and the monthly cost.

    Attributes:
        name (str): Human-readable name of the plan (e.g., 'Free', 'Premium').
        slug (str): URL-friendly unique identifier generated from `name`.
        description (str): Optional detailed description of the plan.
        max_stocks (int): Maximum number of stock assets a user can track.
        allow_crypto (bool): Whether crypto assets are allowed under this plan.
        allow_metals (bool): Whether metals assets are allowed under this plan.
        price_per_month (Decimal): Monthly price for the plan (0 for Free).
        is_active (bool): Determines if the plan is currently available for users.
        created_at (datetime): Timestamp when the plan was created.
        updated_at (datetime): Timestamp when the plan was last updated.    
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Display name for the plan (e.g., Free, Premium, Premium+)."
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Unique slug used for referencing the plan in URLs."
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the plan features."
    )

    # Feature limits
    max_stocks = models.PositiveIntegerField(
        default=10,
        help_text="Maximum number of stocks a user can track under this plan."
    )
    allow_crypto = models.BooleanField(
        default=False,
        help_text="Indicates if this plan allows tracking of crypto assets."
    )
    allow_metals = models.BooleanField(
        default=False,
        help_text="Indicates if this plan allows tracking of metal assets."
    )

    # Pricing
    price_per_month = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        help_text="Monthly price for the plan. Zero for Free tier."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Determines if the plan is available for subscription."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price_per_month']
        verbose_name = 'Plan'
        verbose_name_plural = 'Plans'

    def save(self, *args, **kwargs):
        """
        Automatically generate slug from name if not provided.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Return a human-readable representation of the plan.
        """
        return f"{self.name} (${self.price_per_month})"
