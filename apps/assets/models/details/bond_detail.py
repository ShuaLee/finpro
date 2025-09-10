from django.db import models
from core.types import DomainType

class BondDetail(models.Model):
    asset = models.OneToOneField("assets.Asset", on_delete=models.CASCADE, related_name="bond_detail", limit_choices_to={"asset_type": DomainType.BOND})
    issuer = models.CharField(max_length=200, blank=True, null=True)
    coupon_rate = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    maturity_date = models.DateField(null=True)
    rating = models.CharField(max_length=10, blank=True, null=True)
    last_price = models.DecimalField(max_digits=20, decimal_places=4, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)
    is_custom = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.asset.symbol} ({self.issuer})"