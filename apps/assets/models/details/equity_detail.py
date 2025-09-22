from django.db import models
from assets.models.assets import Asset
from core.types import DomainType


class EquityDetail(models.Model):
    """
    Equity-specific attributes and fundamentals.
    One-to-one with Asset where asset_type = EQUITY.
    Identifiers (ISIN, CUSIP, CIK, etc.) live in AssetIdentifier.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="equity_detail",
        limit_choices_to={"asset_type": DomainType.EQUITY},
    )

    # --- Listing / Exchange Info ---
    exchange = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Stock exchange code (e.g., NYSE, NASDAQ)"
    )
    exchange_full_name = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Full name of the exchange"
    )
    country = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Country of primary listing"
    )
    currency = models.CharField(
        max_length=3, blank=True, null=True,
        help_text="Trading currency (usually matches Asset.currency)"
    )
    ipo_date = models.DateField(blank=True, null=True)

    # --- Classification ---
    sector = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    is_etf = models.BooleanField(default=False)
    is_adr = models.BooleanField(default=False)
    is_mutual_fund = models.BooleanField(default=False)

    # --- Market Data (latest snapshot) ---
    last_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    open_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    previous_close_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    average_volume = models.BigIntegerField(null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    shares_outstanding = models.BigIntegerField(null=True, blank=True)
    beta = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # --- Valuation Ratios (point-in-time) ---
    eps = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    pb_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    ps_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    peg_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # --- Dividend Info (latest only) ---
    dividend_per_share = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    dividend_frequency = models.CharField(max_length=20, blank=True, null=True)
    ex_dividend_date = models.DateField(blank=True, null=True)
    dividend_payout_ratio = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)

    # --- Fund Specific (Mutual Fund / ETF / CEF) ---
    nav = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    expense_ratio = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    fund_family = models.CharField(max_length=100, blank=True, null=True)
    fund_category = models.CharField(max_length=100, blank=True, null=True)
    inception_date = models.DateField(blank=True, null=True)
    total_assets = models.BigIntegerField(null=True, blank=True)
    turnover_ratio = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # ETF-specific
    underlying_index = models.CharField(max_length=100, blank=True, null=True)
    aum = models.BigIntegerField(null=True, blank=True, help_text="Assets under management")
    holdings_count = models.IntegerField(null=True, blank=True)
    tracking_error = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)

    # Closed-End Fund specific
    premium_discount = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)

    # Preferred Shares specific
    preferred_par_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_coupon_rate = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    call_date = models.DateField(blank=True, null=True)

    # --- ESG / Optional ---
    esg_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    carbon_intensity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # --- Listing Status ---
    LISTING_STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("DELISTED", "Delisted"),
        ("SUSPENDED", "Suspended"),
        ("IPO", "IPO Pending"),
        ("CUSTOM", "Custom/Unverified"),
    ]
    listing_status = models.CharField(
        max_length=20,
        choices=LISTING_STATUS_CHOICES,
        default="ACTIVE",
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["exchange"]),
            models.Index(fields=["is_etf"]),
            models.Index(fields=["is_mutual_fund"]),
        ]

    def __str__(self):
        primary_id = self.asset.identifiers.filter(is_primary=True).first()
        return f"{primary_id.value if primary_id else self.asset.name} ({self.exchange})"
