from django.db import models
from django.utils.text import slugify


class Plan(models.Model):
    class Tier(models.TextChoices):
        FREE = "free", "Free"
        PRO = "pro", "Pro"
        WEALTH_MANAGER = "wealth_manager", "Wealth Manager"

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Display name for the plan (e.g., Free, Pro, Wealth Manager).",
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Unique slug used for referencing the plan in URLs.",
    )
    tier = models.CharField(
        max_length=30,
        choices=Tier.choices,
        default=Tier.FREE,
        help_text="Canonical tier classification used for entitlement logic.",
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the plan features.",
    )

    # Legacy feature flags (kept for compatibility while rebuilding higher apps)
    max_stocks = models.PositiveIntegerField(
        default=10,
        help_text="Maximum number of stocks a user can track under this plan.",
    )
    allow_crypto = models.BooleanField(
        default=False,
        help_text="Indicates if this plan allows tracking of crypto assets.",
    )
    allow_metals = models.BooleanField(
        default=False,
        help_text="Indicates if this plan allows tracking of metal assets.",
    )

    # Portfolio/account/holding limits
    max_portfolios = models.PositiveIntegerField(default=1)
    max_accounts_total = models.PositiveIntegerField(null=True, blank=True)
    max_equity_accounts = models.PositiveIntegerField(null=True, blank=True)
    max_holdings_total = models.PositiveIntegerField(null=True, blank=True)
    max_stock_holdings = models.PositiveIntegerField(null=True, blank=True)
    max_crypto_holdings = models.PositiveIntegerField(null=True, blank=True)
    max_real_estate_holdings = models.PositiveIntegerField(null=True, blank=True)

    # Product capability flags
    custom_assets_enabled = models.BooleanField(default=False)
    custom_asset_types_enabled = models.BooleanField(default=False)
    custom_schemas_enabled = models.BooleanField(default=False)
    advanced_analytics_enabled = models.BooleanField(default=False)
    allocations_enabled = models.BooleanField(default=False)
    client_mode_enabled = models.BooleanField(default=False)
    team_members_enabled = models.BooleanField(default=False)

    is_public = models.BooleanField(
        default=True,
        help_text="Public plans are visible to users in the plan listing endpoint.",
    )

    price_per_month = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        help_text="Monthly price for the plan. Zero for Free tier.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Determines if the plan is available for subscription.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price_per_month"]
        verbose_name = "Plan"
        verbose_name_plural = "Plans"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (${self.price_per_month})"
