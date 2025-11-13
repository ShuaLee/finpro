from django.db import models
from assets.models.assets import Asset
from core.types import DomainType


class CryptoDetail(models.Model):
    """
    Reference data for cryptocurrencies from providers.
    Automatically synchronized from FMP.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="crypto_detail",
        limit_choices_to={"asset_type": DomainType.CRYPTO},
    )

    # identity
    base_symbol = models.CharField(max_length=20, null=True, blank=True)
    quote_currency = models.CharField(max_length=10, null=True, blank=True)

    # project metadata (FMP doesn't supply, but room for expansion)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)

    # FMP metadata
    exchange = models.CharField(max_length=50, null=True, blank=True)

    is_custom = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["base_symbol"]),
            models.Index(fields=["quote_currency"]),
        ]

    def __str__(self):
        pid = self.asset.primary_identifier
        return f"{pid.value if pid else self.asset.name}"
