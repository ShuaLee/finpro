import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint

from assets.models.asset_core import Asset


class AssetIdentifier(models.Model):
    """
    Cross-reference identifiers for an asset.

    Rules:
    - An asset may have at most one identifier per type
    - Identifier values are globally unique
    - Equity assets must have exactly one TICKER
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

    class Meta:
        constraints = [
            # One identifier of each type per asset
            UniqueConstraint(
                fields=["asset", "id_type"],
                name="uniq_identifier_type_per_asset",
            ),
        ]
        indexes = [
            models.Index(fields=["id_type", "value"]),
        ]

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------
    def clean(self):
        super().clean()

        allowed = self.asset.asset_type.identifier_rules or []

        if allowed and self.id_type not in allowed:
            raise ValidationError(
                f"Identifier type '{self.id_type}' is not valid for asset type "
                f"'{self.asset.asset_type.slug}'. Allowed: {allowed}"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_type}: {self.value}"
