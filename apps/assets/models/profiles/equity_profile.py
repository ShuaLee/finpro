from django.db import models
from django.core.exceptions import ValidationError

from apps.assets.models.asset_core.asset import Asset
from assets.models.classifications.sector import Sector
from assets.models.classifications.industry import Industry
from assets.models.exchanges import Exchange
from fx.models.country import Country


class EquityProfile(models.Model):
    """
    Stores metadata + market data for equity assets.
    Shares primary key with Asset (1:1).
    """

    asset = models.OneToOneField(
        Asset,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="equity_profile",
    )

    # -------------------------------------------------
    # RELATIONSHIPS
    # -------------------------------------------------
    exchange = models.ForeignKey(
        Exchange, null=True, blank=True, on_delete=models.SET_NULL
    )
    sector = models.ForeignKey(
        Sector, null=True, blank=True, on_delete=models.SET_NULL
    )
    industry = models.ForeignKey(
        Industry, null=True, blank=True, on_delete=models.SET_NULL
    )
    country = models.ForeignKey(
        Country, null=True, blank=True, on_delete=models.SET_NULL
    )

    # -------------------------------------------------
    # PROFILE DATA
    # -------------------------------------------------
    company_name = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    # -------------------------------------------------
    # MARKET DATA (slow-changing)
    # -------------------------------------------------
    price = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    beta = models.FloatField(null=True, blank=True)
    last_dividend = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    ipo_date = models.DateField(null=True, blank=True)

    # -------------------------------------------------
    # MARKET DATA (fast-moving - quote)
    # -------------------------------------------------
    change = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    change_percent = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    avg_volume = models.BigIntegerField(null=True, blank=True)

    # -------------------------------------------------
    # FLAGS
    # -------------------------------------------------
    is_etf = models.BooleanField(default=False)
    is_adr = models.BooleanField(default=False)
    is_fund = models.BooleanField(default=False)

    # From FMP: true if actively trading
    is_actively_trading = models.BooleanField(default=True)

    # Future: optional admin-only override
    # listing_status = models.CharField(max_length=20, default="ACTIVE")

    last_synced = models.DateTimeField(auto_now=True)

    # -------------------------------------------------
    # META
    # -------------------------------------------------
    class Meta:
        verbose_name = "Equity Profile"
        verbose_name_plural = "Equity Profiles"
        ordering = ["asset__name"]
        indexes = [
            models.Index(fields=["exchange"]),
            models.Index(fields=["sector"]),
            models.Index(fields=["industry"]),
            models.Index(fields=["is_actively_trading"]),
        ]

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------
    def clean(self):
        asset_type = self.asset.asset_type.slug
        if asset_type != "equity":
            raise ValidationError(
                f"EquityProfile can only be attached to AssetType 'equity', not '{asset_type}'."
            )

    def __str__(self):
        ident = self.asset.primary_identifier
        return ident.value if ident else str(self.asset.id)
