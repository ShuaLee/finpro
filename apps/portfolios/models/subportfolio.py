from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from portfolios.config import SUBPORTFOLIO_CONFIG
from portfolios.models.portfolio import Portfolio


class SubPortfolio(models.Model):
    """
    Unified SubPortfolio model that replaces StockPortfolio, CryptoPortfolio,
    MetalPortfolio, and CustomPortfolio.

    The available types and their defaults are defined in SUBPORTFOLIO_CONFIG.
    """

    # Choices are dynamically built from config
    TYPES = [(key, cfg["default_name"])
             for key, cfg in SUBPORTFOLIO_CONFIG.items()]

    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="subportfolios"
    )
    type = models.CharField(max_length=50, choices=TYPES)
    name = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("portfolio", "type", "slug")
        app_label = "portfolios"

    def __str__(self):
        return f"{self.name or self.get_type_display()} for {self.portfolio.profile.user.email}"

    def clean(self):
        """
        Auto-fill name/slug if not provided.
        """
        cfg = SUBPORTFOLIO_CONFIG.get(self.type, {})

        # Default name
        if not self.name:
            self.name = cfg.get(
                "default_name", f"{self.type.capitalize()} Portfolio")

        # Default slug
        if not self.slug:
            self.slug = slugify(self.name or f"{self.type}-portfolio")

        # Enforce uniqueness: only one stock/crypto/metal per portfolio
        if cfg.get("unique", False):
            qs = SubPortfolio.objects.filter(
                portfolio=self.portfolio, type=self.type)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    f"Only one {self.get_type_display()} is allowed per portfolio.")

        super().clean()
