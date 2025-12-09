from django.db import models
from django.core.exceptions import ValidationError

from apps.assets.models.asset_core.asset import Asset, AssetType


class BondDetail(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="bond_detail",
    )

    # ----- Identification -----
    issuer = models.CharField(max_length=200, blank=True, null=True)
    cusip = models.CharField(max_length=12, blank=True, null=True)
    isin = models.CharField(max_length=12, blank=True, null=True)
    bond_type = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # ----- Coupon & Cash Flows -----
    coupon_rate = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True)
    coupon_frequency = models.CharField(max_length=20, blank=True, null=True)
    issue_date = models.DateField(null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    call_date = models.DateField(null=True, blank=True)

    # ----- Market Data -----
    last_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    yield_to_maturity = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    yield_to_call = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    current_yield = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    accrued_interest = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True, null=True)

    # ----- Credit & Risk -----
    rating = models.CharField(max_length=10, blank=True, null=True)
    duration = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    convexity = models.DecimalField(
        max_digits=12, decimal_places=6, null=True, blank=True)

    # ----- Size & Liquidity -----
    par_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    issue_size = models.BigIntegerField(null=True, blank=True)
    outstanding_amount = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    # ----- Custom Marker -----
    is_custom = models.BooleanField(default=False)

    class Meta:
        constraints = [
            # Unique ISIN when not null
            models.UniqueConstraint(
                fields=["isin"],
                name="uniq_bond_isin",
                condition=models.Q(isin__isnull=False),
            ),
            # Unique CUSIP when not null
            models.UniqueConstraint(
                fields=["cusip"],
                name="uniq_bond_cusip",
                condition=models.Q(cusip__isnull=False),
            ),
        ]

    # --------------------------------------
    # Validation: Make sure asset_type= bond
    # --------------------------------------
    def clean(self):
        super().clean()

        if self.asset.asset_type.slug != "bond":
            raise ValidationError(
                f"BondDetail can only be attached to assets with type slug='bond', "
                f"but this asset has slug='{self.asset.asset_type.slug}'."
            )

    # --------------------------------------
    # Display
    # --------------------------------------
    def __str__(self):
        pid = self.asset.primary_identifier
        return pid.value if pid else (self.cusip or self.isin or "Bond")
