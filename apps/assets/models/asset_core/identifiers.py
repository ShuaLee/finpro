import uuid

from django.core.exceptions import ValidationError
from django.db import models

from assets.models.asset_core import Asset


class AssetIdentifier(models.Model):
    """
    Cross-reference identifiers for an asset.
    An asset can have multiple identifiers (Ticker, ISIN, CUSIP, etc.).
    Domain-specific validation ensures only valid identifiers per asset type.
    """
    class IdentifierType(models.TextChoices):
        # --- Equities ---
        TICKER = "TICKER", "Ticker"
        ISIN = "ISIN", "ISIN"
        CUSIP = "CUSIP", "CUSIP"
        CIK = "CIK", "CIK"

        # --- Crypto ---
        BASE_SYMBOL = "BASE_SYMBOL", "Base Symbol"
        PAIR_SYMBOL = "PAIR_SYMBOL", "Pair Symbol"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="identifiers",
    )
    id_type = models.CharField(
        max_length=30,
        choices=IdentifierType.choices,
        db_index=True,
    )
    value = models.CharField(max_length=100, db_index=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Marks the main identifier to display/use in trading.",
    )

    class Meta:
        unique_together = ("id_type", "value")
        indexes = [
            models.Index(fields=["id_type", "value"]),
            models.Index(fields=["asset", "is_primary"]),
        ]

    # ---------------------------------------------------------------
    # Validation rules: enforce one primary + domain-specific id types
    # ---------------------------------------------------------------
    def clean(self):
        super().clean()

        # Enforce exactly one primary identifier per asset
        if self.is_primary:
            existing_primary = self.asset.identifiers.filter(is_primary=True)
            if self.pk:
                existing_primary = existing_primary.exclude(pk=self.pk)
            if existing_primary.exists():
                raise ValidationError(
                    "An asset can only have one primary identifier."
                )

        # Use AssetType.identifier_rules instead of domain registry
        allowed = self.asset.asset_type.identifier_rules or []

        if allowed and self.id_type not in allowed:
            raise ValidationError(
                f"Identifier type '{self.id_type}' is not valid for asset type "
                f"'{self.asset.asset_type.slug}'. Allowed: {allowed}"
            )

    def save(self, *args, **kwargs):
        # Validate before saving
        self.clean()

        # Auto-mark first identifier as primary if none exist
        if not self.asset.identifiers.exists():
            self.is_primary = True

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_type}: {self.value}"
