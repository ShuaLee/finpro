from datetime import timedelta
from django.db import models
from django.utils import timezone
from assets.models.assets import Asset
from core.types import DomainType


class MarketDataCache(models.Model):
    """
    Cached real-time market snapshot for tradable assets (Equities, Crypto, Bonds, Metals, etc.)

    Design philosophy:
    - One unified model for all asset classes (nullable fields for non-applicable data)
    - Represents *current* quote state — not historical or analytic data
    - Updated periodically via EquitySyncService or equivalent sync service
    """

    # -------------------------------------------------------------------------
    # Core fields (applies to all tradable asset types)
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Equity-specific metrics (will remain NULL for crypto, metals, etc.)
    # -------------------------------------------------------------------------
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    eps = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    dividend_yield = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    dividend_per_share = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)

    # -------------------------------------------------------------------------
    # Optional/extended metrics (can be used by any type, if supported)
    # -------------------------------------------------------------------------
    avg_volume = models.BigIntegerField(null=True, blank=True)
    year_high = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    year_low = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)

    # -------------------------------------------------------------------------
    # Future-reserved metrics (for bonds, commodities, etc.)
    # -------------------------------------------------------------------------
    yield_to_maturity = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    coupon_rate = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    metal_purity = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True)

    # -------------------------------------------------------------------------
    # Refresh tracking
    # -------------------------------------------------------------------------
    last_synced = models.DateTimeField(auto_now=True)

    def __str__(self):
        pid = getattr(self.asset, "primary_identifier", None)
        sym = pid.value if pid else self.asset.name
        return f"{sym}: {self.last_price or 'N/A'}"

    class Meta:
        indexes = [
            models.Index(fields=["last_synced"]),
            models.Index(fields=["asset"]),
        ]
        verbose_name = "Market Data Cache"
        verbose_name_plural = "Market Data Cache"

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    def is_stale(self, ttl_minutes: int = 5) -> bool:
        """Return True if data is older than given minutes."""
        if not self.last_synced:
            return True
        return timezone.now() - self.last_synced > timedelta(minutes=ttl_minutes)
