from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from core.types import DomainType
from portfolios.models.portfolio import Portfolio


class SubPortfolio(models.Model):
    """
    Unified SubPortfolio model that replaces StockPortfolio, CryptoPortfolio,
    MetalPortfolio, and CustomPortfolio.

    The available types and their defaults are defined in DOMAIN_TYPE_REGISTRY.
    """
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="subportfolios"
    )
    type = models.CharField(max_length=50, choices=DomainType.choices)
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
        from core.types import DOMAIN_TYPE_REGISTRY

        domain_meta = DOMAIN_TYPE_REGISTRY.get(self.type, {})

        # Default name
        if not self.name:
            self.name = domain_meta.get(
                "default_name", f"{self.type.capitalize()} Portfolio")

        # Default slug
        if not self.slug:
            self.slug = slugify(self.name or f"{self.type}-portfolio")

        # Enforce uniqueness: only one stock/crypto/metal per portfolio
        if domain_meta.get("unique", False):
            qs = SubPortfolio.objects.filter(
                portfolio=self.portfolio, type=self.type)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    f"Only one {self.get_type_display()} is allowed per portfolio.")

        super().clean()

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # check if creating new subportfolio

        if not is_new:
            # Prevent type changes
            old = SubPortfolio.objects.filter(
                pk=self.pk
            ).values_list("type", flat=True).first()
            if old and old != self.type:
                raise ValidationError(
                    "SubPortfolio type cannot be changed once created."
                )

        super().save(*args, **kwargs)

        # 🛠 Generate schemas on creation
        if is_new:
            from schemas.services.schema_generator import SchemaGenerator
            generator = SchemaGenerator(self, self.type)
            generator.initialize()
