from django.db import models

from assets.models.core import Asset


class AssetPrice(models.Model):
    """
    Stores the CURRENT price of an asset.
    Overwritten on each update — no historical data.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="price",
    )

    price = models.DecimalField(
        max_digits=20,
        decimal_places=6,
    )

    # Where the price came from (FMP, manual, derived, etc.)
    source = models.CharField(
        max_length=50,
        defaults="FMP",
    )

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["last_updated"]),
            models.Index(fields=["source"]),
        ]

    def __str__(self):
        return f"{self.asset_id} = {self.price} ({self.source})"