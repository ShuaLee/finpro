from django.db import models
from assets.models.asset import Asset
from core.types import DomainType


class EquityDetail(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="equity_detail",
        limit_choices_to={"asset_type": DomainType.EQUITY}
    )

    # --- Identification ---
    exchange = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="Stock exchange short code (e.g., NYSE, NASDAQ)"
    )
    exchange_full_name = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Full name of the exchange"
    )
    currency = models.CharField(max_length=3, blank=True, null=True)
    country = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Country of primary listing"
    )
    isin = models.CharField(
        max_length=12, blank=True, null=True,
        help_text="ISIN identifier (international securities)"
    )
    cusip = models.CharField(
        max_length=12, blank=True, null=True,
        help_text="CUSIP identifier (US securities)"
    )
    cik = models.CharField(max_length=10, null=True, blank=True)
    ipo_date = models.DateField(blank=True, null=True)

    # --- Classification ---
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    is_etf = models.BooleanField(default=False)
    is_adr = models.BooleanField(default=False)
    is_mutual_fund = models.BooleanField(
        default=False,
        help_text="True if this asset is a mutual fund"
    )

    # --- Market Data (latest) ---
    last_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        help_text="Last synced market price"
    )
    open_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    previous_close_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    average_volume = models.BigIntegerField(null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    shares_outstanding = models.BigIntegerField(null=True, blank=True)
    beta = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)

    # --- Valuation Ratios ---
    eps = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    pb_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    ps_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    peg_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)

    # --- Dividend Info ---
    dividend_per_share = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    dividend_yield = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True)
    dividend_frequency = models.CharField(max_length=20, blank=True, null=True)
    ex_dividend_date = models.DateField(blank=True, null=True)
    dividend_payout_ratio = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True)

    # --- Mutual Fund Specific ---
    nav = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True,
        help_text="Net Asset Value per share"
    )
    expense_ratio = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text="Annual fee ratio"
    )
    fund_family = models.CharField(max_length=100, blank=True, null=True)
    fund_category = models.CharField(max_length=100, blank=True, null=True)
    inception_date = models.DateField(blank=True, null=True)
    total_assets = models.BigIntegerField(null=True, blank=True)
    turnover_ratio = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True)

    # --- ETF Specific ---
    underlying_index = models.CharField(max_length=100, blank=True, null=True)
    aum = models.BigIntegerField(
        null=True, blank=True, help_text="Assets under management")
    holdings_count = models.IntegerField(null=True, blank=True)
    tracking_error = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True)

    # --- Closed-End Fund Specific ---
    premium_discount = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text="Premium (+) or discount (-) to NAV, as a ratio"
    )

    # --- Preferred Shares Specific ---
    preferred_par_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Par value of preferred shares"
    )
    preferred_coupon_rate = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text="Coupon rate (%) for preferred shares"
    )
    call_date = models.DateField(
        blank=True, null=True,
        help_text="Earliest call date for callable preferred shares"
    )

    # --- Optional ESG ---
    esg_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True)
    carbon_intensity = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    # --- Custom / System ---
    is_custom = models.BooleanField(
        default=False,
        help_text="True if user-defined (not synced from provider)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["exchange"]),
            models.Index(fields=["is_custom"]),
            models.Index(fields=["is_etf"]),
            models.Index(fields=["is_mutual_fund"]),
        ]

    def __str__(self):
        return f"{self.asset.symbol} ({self.exchange})"
