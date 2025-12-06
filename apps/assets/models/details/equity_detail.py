from django.db import models
from django.core.exceptions import ValidationError

from assets.models.assets import Asset
from fx.models.country import Country


class EquityDetail(models.Model):
    """
    Equity-specific attributes and fundamentals.
    One-to-one with Asset where asset_type.slug = 'equity'.
    Identifiers (ISIN, CUSIP, CIK, etc.) live in AssetIdentifier.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="equity_detail",
        limit_choices_to={"asset_type__slug": "equity"},
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
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equity_listings",
        help_text="Country of primary listing (ISO-3166)."
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
        ("ACTIVE", "Active"),
        ("DELISTED", "Delisted"),
        ("SUSPENDED", "Suspended"),
        ("IPO", "IPO Pending"),
        ("PENDING", "Pending Data"),
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

    # -------------------------------------------------
    # VALIDATION — enforce correct asset type
    # -------------------------------------------------
    def clean(self):
        super().clean()

        if self.asset.asset_type.slug != "equity":
            raise ValidationError(
                f"EquityDetail can only attach to assets with type slug='equity'. "
                f"Got slug='{self.asset.asset_type.slug}'."
            )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset"], name="unique_equity_detail_asset"
            ),
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
