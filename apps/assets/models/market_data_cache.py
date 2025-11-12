from datetime import timedelta
from django.db import models
from django.utils import timezone
from assets.models.assets import Asset
from core.types import DomainType



class MarketDataCache(models.Model):
    """
    Unified price snapshot for any tradable asset.
    Only fields actually relevant to your product.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="market_data",
        limit_choices_to={"asset_type__in": [
            DomainType.EQUITY,
            DomainType.CRYPTO,
            DomainType.BOND,
            DomainType.METAL,
        ]},
    )

    # Core
    last_price = models.DecimalField(max_digits=20, decimal_places=8,
                                     null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)

    # Equity-only metrics (NULL for crypto/metals)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=4,
                                   null=True, blank=True)
    eps = models.DecimalField(max_digits=10, decimal_places=4,
                              null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=10, decimal_places=4,
                                         null=True, blank=True)
    dividend_per_share = models.DecimalField(max_digits=10, decimal_places=4,
                                             null=True, blank=True)

    # Future-proof fields, may be NULL always
    yield_to_maturity = models.DecimalField(max_digits=10, decimal_places=4,
                                            null=True, blank=True)
    coupon_rate = models.DecimalField(max_digits=10, decimal_places=4,
                                      null=True, blank=True)
    metal_purity = models.DecimalField(max_digits=6, decimal_places=3,
                                       null=True, blank=True)

    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["last_synced"]),
            models.Index(fields=["asset"]),
        ]

    def is_stale(self, ttl_minutes=5) -> bool:
        if not self.last_synced:
            return True
        return timezone.now() - self.last_synced > timedelta(minutes=ttl_minutes)

    def __str__(self):
        pid = self.asset.primary_identifier
        sym = pid.value if pid else self.asset.name
        return f"{sym}: {self.last_price or 'N/A'}"