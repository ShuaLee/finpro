from datetime import timedelta
from django.db import models
from django.utils import timezone
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
    last_synced = models.DateTimeField(auto_now=True)

    def __str__(self):
        pid = self.asset.primary_identifier
        return f"{pid.value if pid else self.asset.name}: {self.last_price or 'N/A'}"

    class Meta:
        indexes = [
            models.Index(fields=["last_synced"]),
            models.Index(fields=["asset"]),
        ]

    def is_stale(self, ttl_minutes: int = 5) -> bool:
        """Return True if data is older than given minutes."""
        if not self.last_synced:
            return True
        return timezone.now() - self.last_synced > timedelta(minutes=ttl_minutes)
