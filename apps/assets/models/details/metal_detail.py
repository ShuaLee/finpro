from django.db import models
from django.core.exceptions import ValidationError

from apps.assets.models.asset_core.asset import Asset


class MetalDetail(models.Model):
    """
    Reference data for precious metals, synced from providers.
    One-to-one with Asset where asset_type.slug = 'metal'.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="metal_detail",
        limit_choices_to={"asset_type__slug": "metal"},
    )

    # --- Identification ---
    unit = models.CharField(
        max_length=20,
        default="oz",
        help_text="Measurement unit (e.g., ounce, gram)"
    )
    currency = models.CharField(
        max_length=10, blank=True, null=True,
        help_text="Quote currency (usually USD)"
    )

    # --- Market Data ---
    last_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        help_text="Last synced market price per unit"
    )
    open_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        help_text="Opening price for the trading session"
    )
    day_high = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        help_text="Intraday high"
    )
    day_low = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        help_text="Intraday low"
    )
    previous_close = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        help_text="Previous session close"
    )
    volume = models.BigIntegerField(
        null=True, blank=True,
        help_text="Trading volume if available (may not exist for metals)"
    )

    # --- Custom/System ---
    is_custom = models.BooleanField(
        default=False,
        help_text="True if user-defined (not synced from provider)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["currency"]),
            models.Index(fields=["is_custom"]),
        ]

    # -------------------------------------------------
    # Validation — ensure asset_type.slug matches
    # -------------------------------------------------
    def clean(self):
        super().clean()

        if self.asset.asset_type.slug != "metal":
            raise ValidationError(
                f"MetalDetail can only attach to assets with asset_type.slug='metal'. "
                f"Got '{self.asset.asset_type.slug}'."
            )

    def __str__(self):
        primary_id = self.asset.primary_identifier
        symbol = primary_id.value if primary_id else self.asset.name
        return f"{symbol} ({self.unit})"
