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

    decimals = models.PositiveSmallIntegerField(
        default=8,
        help_text="Number of decimal places supported (BTC=8, ETH=18, etc.)"
    )

    last_price = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True,
        help_text="Last synced market price in quote currency"
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
        return f"{self.asset.symbol} - {self.asset.name}"
