from django.core.exceptions import ValidationError
from django.db import models

from assets.models.core import Asset
from assets.models.equity.exchange import Exchange
from fx.models.country import Country
from fx.models.fx import FXCurrency


class EquityAsset(models.Model):
    """
    Canonical, non-historical equity reference.

    This table represents the CURRENT actively tradable equity universe.
    It is safe to truncate and rebuild multiple times per day.

    Characteristics:
    - One row per active ticker
    - No ownership
    - No historical identity tracking
    - No reconciliation logic
    - Optimized for portfolio valuation

    Source of truth:
    - Provider "actively traded" universe
    - Single-ticker profile endpoint

    Inactive equities are removed from the table entirely.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="equity",
    )

    snapshot_id = models.UUIDField(db_index=True)

    # --------------------------------------------------
    # Identity
    # --------------------------------------------------
    ticker = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Primary trading symbol (e.g. AAPL).",
    )

    name = models.CharField(
        max_length=255,
        help_text="Company or fund name.",
    )

    # --------------------------------------------------
    # Identifiers
    # --------------------------------------------------
    isin = models.CharField(max_length=20, null=True, blank=True)
    cusip = models.CharField(max_length=20, null=True, blank=True)
    cik = models.CharField(max_length=20, null=True, blank=True)

    # --------------------------------------------------
    # Classification
    # --------------------------------------------------
    exchange = models.ForeignKey(
        Exchange,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="equities",
    )

    sector = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
    )

    industry = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        db_index=True,
    )

    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="equities",
    )

    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="equities",
        null=True,
        blank=True,
    )

    # --------------------------------------------------
    # Company metadata
    # --------------------------------------------------
    website = models.URLField(
        max_length=500,
        null=True,
        blank=True,
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    image_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
    )

    # --------------------------------------------------
    # Financial metadata
    # --------------------------------------------------
    market_cap = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Market capitalization in quote currency.",
    )

    beta = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )

    last_dividend = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Last dividend paid per share.",
    )

    ipo_date = models.DateField(
        null=True,
        blank=True,
    )

    # --------------------------------------------------
    # Flags
    # --------------------------------------------------
    is_etf = models.BooleanField(default=False)
    is_adr = models.BooleanField(default=False)
    is_fund = models.BooleanField(default=False)
    is_actively_trading = models.BooleanField(default=True)

    # -------------------------
    # Provider metadata
    # -------------------------
    last_synced = models.DateTimeField(
        auto_now=True,
        help_text="Last time this equity was fetched from the data provider."
    )

    class Meta:
        ordering = ["ticker"]
        indexes = [
            models.Index(fields=["ticker"]),
            models.Index(fields=["exchange"]),
            models.Index(fields=["sector"]),
            models.Index(fields=["industry"]),
        ]

    def clean(self):
        super().clean()

        # Allow partial construction (factory/admin/migrations)
        if not self.asset:
            return

        if self.asset.asset_type.slug != "equity":
            raise ValidationError(
                "Equity may only be attached to assets of type 'equity'."
            )

    def __str__(self) -> str:
        return f"{self.ticker} – {self.name}"
