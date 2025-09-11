from django.db import models
from assets.models.asset import Asset
from core.types import DomainType


class CustomDetail(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="custom_detail",
        limit_choices_to={"asset_type": DomainType.CUSTOM},
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.asset.name
