from django.db import models
from core.types import DomainType

class CustomDetail(models.Model):
    asset = models.OneToOneField("assets.Asset", on_delete=models.CASCADE, related_name="custom_detail", limit_choices_to={"asset_type": DomainType.CUSTOM})
    description = models.TextField()
    origin = models.CharField(max_length=200, blank=True)
    purchase_price = models.DecimalField(...)
    last_price = models.DecimalField(...)
    unit = models.CharField(max_length=50, default="unit")