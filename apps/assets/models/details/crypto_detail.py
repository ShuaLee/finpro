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

    # Decimal place precision
    quantity_precision = models.PositiveIntegerField(default=18)   # BTC=8, XRP=6, etc

    # project metadata (FMP doesn't supply, but room for expansion)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)

    # FMP metadata
    exchange = models.CharField(max_length=50, null=True, blank=True)

    is_custom = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def base_symbol(self):
        ident = self.asset.identifiers.filter(
            id_type="BASE_SYMBOL"
        ).first()
        return ident.value if ident else None

    @property
    def pair_symbol(self):
        ident = self.asset.identifiers.filter(
            id_type="PAIR_SYMBOL"
        ).first()
        return ident.value if ident else None

    def __str__(self):
        pid = self.asset.primary_identifier
        return f"{pid.value if pid else self.asset.name}"
