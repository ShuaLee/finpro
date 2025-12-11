from django.db import models

from assets.models.asset_core import Asset


class AssetPrice(models.Model):
    """
    Stores the current price of an asset.
    Overwritten on each update — no historical data kept.
    """
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="asset_price",
    )

    price = models.DecimalField(max_digits=20, decimal_places=6)

    # e.g. "FMP", "manual", "user", "derived"
    source = models.CharField(max_length=50, default="FMP")

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset} = {self.price}"
