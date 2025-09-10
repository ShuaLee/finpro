from django.db import models
from core.types import DomainType

class RealEstateDetail(models.Model):
    asset = models.OneToOneField("assets.Asset", on_delete=models.CASCADE, related_name="real_estate_detail", limit_choices_to={"asset_type": DomainType.REAL_ESTATE})
    location = models.CharField(max_length=255)
    property_type = models.CharField(max_length=100)  # e.g. Residential, Commercial
    purchase_price = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    estimated_value = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    rental_income = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")

    def __str__(self):
        return f"{self.asset.symbol} ({self.location})"