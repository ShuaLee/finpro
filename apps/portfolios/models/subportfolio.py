from django.db import models
from django.utils.text import slugify
from portfolios.models.portfolio import Portfolio


class SubPortfolio(models.Model):
    """
    Unified subportfolio model that replaces StockPortfolio, CryptoPortfolio,
    MetalPortfolio, and CustomPortfolio.

    Responsibilities:
    - Belongs to a main Portfolio.
    - Has a `type` (e.g., stock, crypto, metal, custom).
    - Enforces uniqueness rules per type (via config).
    - Optional name/slug for custom portfolios.
    """

    class SubPortfolioType(models.TextChoices):
        STOCK = "stock", "Stock"
        CRYPTO = "crypto", "Crypto"
        METAL = "metal", "Metal"
        CUSTOM = "custom", "Custom"

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="subportfolios"
    )
    type = models.CharField(max_length=50, choices=SubPortfolioType.choices)
    name = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("portfolio", "type", "slug")
        app_label = "portfolios"

    def __str__(self):
        if self.type == self.SubPortfolioType.CUSTOM:
            return f"{self.portfolio.profile.user.email} | {self.name}"
        return f"{self.get_type_display()} Portfolio for {self.portfolio.profile.user.email}"

    def clean(self):
        """
        Ensure slug for custom subportfolios.
        Uniqueness/allowed-type constraints will be enforced by service/manager.
        """
        if self.type == self.SubPortfolioType.CUSTOM:
            if not self.slug:
                self.slug = slugify(self.name or "")
            if not self.slug:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    "CustomPortfolio must have a non-empty slug.")
        super().clean()
