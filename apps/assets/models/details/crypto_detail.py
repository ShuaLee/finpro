from django.db import models
from assets.models.asset import Asset
from core.types import DomainType


class CryptoDetail(models.Model):
    """
    Reference data for cryptocurrencies, synced from FMP or another provider.
    One-to-one with Asset where asset_type = CRYPTO.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="crypto_detail",
        limit_choices_to={"asset_type": DomainType.CRYPTO},
    )

    # Identification
    exchange = models.CharField(max_length=50, null=True, blank=True)
    currency = models.CharField(
        max_length=10, blank=True, null=True,
        help_text="Quote currency (usually USD)"
    )
    decimals = models.PositiveSmallIntegerField(
        default=8,
        help_text="Number of decimal places supported (BTC=8, ETH=18, etc.)"
    )

    # Market data
    last_price = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True,
        help_text="Last synced market price"
    )
    market_cap = models.BigIntegerField(null=True, blank=True)
    volume_24h = models.BigIntegerField(null=True, blank=True)
    circulating_supply = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True
    )
    total_supply = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True
    )

    day_high = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True)
    day_low = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True)
    year_high = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True)
    year_low = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True)

    open_price = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True)
    previous_close = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True)
    changes_percentage = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text="24h change percentage"
    )

    # Project metadata
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)

    # Custom/system
    is_custom = models.BooleanField(
        default=False,
        help_text="True if user-defined (not synced from provider)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["exchange"]),
            models.Index(fields=["currency"]),
            models.Index(fields=["is_custom"]),
        ]

    def __str__(self):
        return f"{self.asset.symbol} - {self.asset.name}"
