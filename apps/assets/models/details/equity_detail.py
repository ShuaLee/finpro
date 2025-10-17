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

    ipo_date = models.DateField(blank=True, null=True)

    # --- Classification ---
    sector = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    is_etf = models.BooleanField(default=False)
    is_adr = models.BooleanField(default=False)
    is_mutual_fund = models.BooleanField(default=False)

    # --- Listing Status ---
    LISTING_STATUS_CHOICES = [
        ("ACTIVE", "Active"),                # Normal tradable equity
        ("DELISTED", "Delisted"),            # Removed from market
        ("SUSPENDED", "Suspended"),          # Trading halted/paused
        ("IPO", "IPO Pending"),              # Known IPO, not yet active
        # Exists, but not yet hydrated (profile/quote missing)
        ("PENDING", "Pending Data"),
        # Custom ticker conflicts with new real asset
        ("COLLISION", "Collision"),
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
        constraints = [
            models.UniqueConstraint(
                fields=["asset"], name="unique_equity_detail_asset")
        ]
        indexes = [
            models.Index(fields=["exchange"]),
            models.Index(fields=["is_etf"]),
            models.Index(fields=["is_mutual_fund"]),
        ]

    def __str__(self):
        primary_id = self.asset.identifiers.filter(is_primary=True).first()
        exch = self.exchange or "N/A"
        return f"{primary_id.value if primary_id else self.asset.name} ({exch})"
