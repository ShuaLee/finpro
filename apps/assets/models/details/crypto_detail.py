from django.db import models
from assets.models.assets import Asset
from core.types import DomainType


class CryptoDetail(models.Model):
    """
    Stable metadata for cryptocurrencies.
    (FMP does not provide real profiles, only symbol/name/exchange.)
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="crypto_detail",
        limit_choices_to={"asset_type": DomainType.CRYPTO},
    )

    exchange = models.CharField(max_length=50, null=True, blank=True)

    decimals = models.PositiveSmallIntegerField(
        default=8,
        help_text="Number of decimal places supported (BTC=8, ETH=18)."
    )

    # Optional enrichment (not provided by FMP)
    logo_url = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["exchange"]),
            models.Index(fields=["is_custom"]),
        ]

    def __str__(self):
        primary = self.asset.primary_identifier
        return f"{primary.value if primary else self.asset.name} (Crypto)"