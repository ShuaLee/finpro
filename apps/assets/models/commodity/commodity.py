from django.core.exceptions import ValidationError
from django.db import models

from assets.models.core import Asset
from fx.models.fx import FXCurrency


class CommodityAsset(models.Model):
    """
    Canonical, non-historical commodity reference.

    This table represents the CURRENT actively tradable commodity universe
    as provided by the data provider (e.g. FMP).

    Characteristics:
    - One row per active commodity symbol
    - No ownership or account semantics
    - Safe to truncate and rebuild multiple times per day
    - Optimized for valuation and exposure tracking
    - Referenced by domain-specific holdings (e.g. precious metals)

    Inactive commodities are removed from the table entirely.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="commodity",
        primary_key=True,
    )

    # -------------------------
    # Identifiers
    # -------------------------
    symbol = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Provider symbol (e.g. GCUSD, CLUSD, SIUSD).",
    )

    name = models.CharField(
        max_length=200,
        help_text="Human-readable commodity name from provider.",
    )

    # -------------------------
    # Market metadata
    # -------------------------
    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="commodities",
        null=True,
        blank=True,
        help_text="Trading currency for this commodity.",
    )

    trade_month = models.CharField(
        max_length=10,
        blank=True,
        help_text="Front or active contract month as reported by provider.",
    )

    # -------------------------
    # Provider metadata
    # -------------------------
    last_synced = models.DateTimeField(
        auto_now=True,
        help_text="Last time this commodity was fetched from the data provider.",
    )

    class Meta:
        ordering = ["symbol"]
        verbose_name_plural = "Commodities"
        indexes = [
            models.Index(fields=["symbol"]),
        ]

    def clean(self):
        if self.asset.asset_type.slug != "commodity":
            raise ValidationError(
                "CommodityAsset may only be attached to assets of type 'commodity'."
            )

    def __str__(self) -> str:
        return f"{self.symbol} – {self.name}"
