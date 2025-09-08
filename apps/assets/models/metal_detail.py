from django.db import models
from assets.models.asset import Asset, AssetType


class MetalDetail(models.Model):
    """
    Reference data for precious metals, synced from FMP or another provider.
    One-to-one with Asset where asset_type = METAL.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="metal_detail",
        limit_choices_to={"asset_type": AssetType.METAL},
    )

    unit = models.CharField(
        max_length=20,
        default="oz",
        help_text="Measurement unit (e.g., ounce, gram)"
    )
    last_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        help_text="Last synced market price per unit"
    )
    currency = models.CharField(
        max_length=10, blank=True, null=True,
        help_text="Quote currency (usually USD)"
    )

    is_custom = models.BooleanField(
        default=False,
        help_text="True if user-defined (not synced from provider)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset.symbol} ({self.unit})"
