from django.db import models
from assets.models.asset import Asset, AssetType


class StockDetail(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="stock_detail",
        limit_choices_to={"asset_type": AssetType.STOCK}
    )

    # Identification
    exchange = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="Stock exchange (e.g., NYSE, NASDAQ)"
    )
    currency = models.CharField(max_length=3, blank=True, null=True)

    # Market classification
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    is_etf = models.BooleanField(default=False)
    is_adr = models.BooleanField(default=False)

    # Market metrics
    last_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        help_text="Last synced market price"
    )
    volume = models.BigIntegerField(null=True, blank=True)
    average_volume = models.BigIntegerField(null=True, blank=True)
    dividend_yield = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True
    )
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )

    # Custom flag
    is_custom = models.BooleanField(
        default=False,
        help_text="True if user-defined (not synced from FMP)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["exchange"]),
            models.Index(fields=["is_custom"]),
        ]

    def __str__(self):
        return f"{self.asset.symbol} ({self.exchange})"

