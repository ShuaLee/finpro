from django.db import models
from core.types import DomainType


class BondDetail(models.Model):
    asset = models.OneToOneField(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="bond_detail",
        limit_choices_to={"asset_type": DomainType.BOND},
    )

    # Identification
    issuer = models.CharField(max_length=200, blank=True, null=True)
    cusip = models.CharField(max_length=12, blank=True, null=True)
    isin = models.CharField(max_length=12, blank=True, null=True)
    # Govt, corporate, muni...
    bond_type = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # Coupon & cash flows
    coupon_rate = models.DecimalField(
        max_digits=6, decimal_places=4, null=True)
    coupon_frequency = models.CharField(
        max_length=20, blank=True, null=True)  # e.g., Annual, Semiannual
    issue_date = models.DateField(null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    call_date = models.DateField(null=True, blank=True)

    # Market data
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

    # Credit & risk
    rating = models.CharField(max_length=10, blank=True, null=True)
    duration = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    convexity = models.DecimalField(
        max_digits=12, decimal_places=6, null=True, blank=True)

    # Size & liquidity
    par_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    issue_size = models.BigIntegerField(null=True, blank=True)
    outstanding_amount = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    # Custom/system
    is_custom = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.asset.symbol or self.cusip} ({self.issuer})"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["isin"],
                name="uniq_bond_isin",
                condition=~models.Q(isin=None)
            ),
            models.UniqueConstraint(
                fields=["cusip"],
                name="uniq_bond_cusip",
                condition=~models.Q(cusip=None)
            ),
        ]
