from django.db import models
from assets.models.assets import Asset
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
