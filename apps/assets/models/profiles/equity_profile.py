# assets/models/profiles/equity_profile.py
from django.db import models
from django.core.exceptions import ValidationError
from assets.models.asset_core import Asset
from assets.models.classifications.sector import Sector
from assets.models.classifications.industry import Industry
from assets.models.exchanges import Exchange
from fx.models.country import Country


class EquityProfile(models.Model):
    """
    Stable metadata and slow-changing attributes for equity assets.
    1:1 with Asset.
    """

    asset = models.OneToOneField(
        Asset,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="equity_profile"
    )

    name = models.CharField(max_length=255, null=True, blank=True)

    # Relationships
    exchange = models.ForeignKey(
        Exchange, null=True, blank=True, on_delete=models.SET_NULL)
    sector = models.ForeignKey(
        Sector, null=True, blank=True, on_delete=models.SET_NULL)
    industry = models.ForeignKey(
        Industry, null=True, blank=True, on_delete=models.SET_NULL)
    country = models.ForeignKey(
        Country, null=True, blank=True, on_delete=models.SET_NULL)

    # Stable metadata
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    # Slow-changing market data
    market_cap = models.BigIntegerField(null=True, blank=True)
    beta = models.FloatField(null=True, blank=True)
    last_dividend = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True)
    ipo_date = models.DateField(null=True, blank=True)

    # Flags
    is_etf = models.BooleanField(default=False)
    is_adr = models.BooleanField(default=False)
    is_fund = models.BooleanField(default=False)
    is_actively_trading = models.BooleanField(default=True)

    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        if self.asset.asset_type.slug != "equity":
            raise ValidationError(
                "EquityProfile may only attach to equity assets.")
        
    @property
    def ticker(self):
        ident = self.asset.identifiers.filter(id_type="TICKER").first()
        return ident.value if ident else None

    @property
    def display_name(self):
        """
        Equity display format:
        TICKER – Company Name
        """
        ticker = self.ticker
        name = self.name

        if ticker and name:
            return f"{ticker} – {name}"
        if ticker:
            return ticker
        if name:
            return name

        return str(self.asset.id)

    def __str__(self):
        ident = self.asset.primary_identifier
        return ident.value if ident else str(self.asset.id)
