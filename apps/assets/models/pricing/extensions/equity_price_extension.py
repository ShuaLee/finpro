from django.core.exceptions import ValidationError
from django.db import models


class EquityPriceExtension(models.Model):
    """
    Stores fast-moving quote fields for equities.
    Extends the single AssetPrice record.
    """
    asset_price = models.OneToOneField(
        "assets.AssetPrice",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="equity_extension",
    )

    change = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True)
    change_percent = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    avg_volume = models.BigIntegerField(null=True, blank=True)

    def clean(self):
        asset = self.price_record.asset
        if asset.asset_type.slug != "equity":
            raise ValidationError(
                "EquityPriceExtension may only attach to equity assets.")

    def __str__(self):
        return f"Equity quote data for {self.price_record.asset}"
