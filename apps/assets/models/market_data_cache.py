from django.db import models
from assets.models.assets import Asset
from core.types import DomainType


class MarketDataCache(models.Model):
    """
    Short-term cached market data for tradable assets.
    Updated periodically via FMP (or other sources).
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="market_data",
        limit_choices_to={
            "asset_type__in": [
                DomainType.EQUITY,
                DomainType.BOND,
                DomainType.CRYPTO,
                DomainType.METAL,
            ]
        },
    )

    # --- Quote Info ---
    last_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    change = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    change_percent = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    previous_close = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    open_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)

    # --- Refresh Tracking ---
    last_synced = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        pid = self.asset.primary_identifier
        return f"{pid.value if pid else self.asset.name}: {self.last_price or 'N/A'}"

    class Meta:
        indexed = [
            models.Index(fields=["last_synced"])
        ]
