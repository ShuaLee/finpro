from django.db import models
from django.core.exceptions import ValidationError
from core.types import DomainType


class Asset(models.Model):
    asset_type = models.CharField(
        max_length=20,
        choices=DomainType.choices,
        db_index=True,
    )
    symbol = models.CharField(
        max_length=20,
        db_index=True,
        blank=True,
        null=True,
        help_text="Ticker or unique code (required for traded assets, optional for real estate/custom)."
    )
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name (company, property, or custom asset)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset_type", "symbol"],
                name="uniq_asset_type_symbol",
                condition=~models.Q(symbol=None)  # only enforce uniqueness when symbol is present
            )
        ]

    def clean(self):
        """Enforce symbol rules depending on asset type."""
        if self.asset_type in {
            DomainType.EQUITY,
            DomainType.CRYPTO,
            DomainType.METAL,
            DomainType.BOND,
        } and not self.symbol:
            raise ValidationError(f"Symbol is required for {self.asset_type} assets")
        # Real estate & custom may omit symbol

    def __str__(self):
        return f"{self.symbol or self.name} ({self.asset_type})"