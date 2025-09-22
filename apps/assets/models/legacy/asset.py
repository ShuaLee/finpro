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
                # only enforce uniqueness when symbol is present
                condition=~models.Q(symbol=None)
            )
        ]

    def clean(self):
        super().clean()

        # 1. Enforce symbol rules for traded types
        if self.asset_type in {
            DomainType.EQUITY,
            DomainType.CRYPTO,
            DomainType.METAL,
            DomainType.BOND,
        } and not self.symbol:
            raise ValidationError(
                f"Symbol is required for {self.asset_type} assets."
            )

        # 2. Validate: only one detail model exists
        detail_relations = {
            DomainType.EQUITY: getattr(self, "equity_detail", None),
            DomainType.BOND: getattr(self, "bond_detail", None),
            DomainType.CRYPTO: getattr(self, "crypto_detail", None),
            DomainType.METAL: getattr(self, "metal_detail", None),
            DomainType.REAL_ESTATE: getattr(self, "real_estate_detail", None),
            DomainType.CUSTOM: getattr(self, "custom_detail", None),
        }

        # Allow zero or one detail — only error if there's > 1
        detail_instances = [
            v for v in detail_relations.values() if v is not None]
        if len(detail_instances) > 1:
            raise ValidationError(
                "An asset can only have one detail model attached."
            )

    def __str__(self):
        return f"{self.symbol or self.name} ({self.asset_type})"
