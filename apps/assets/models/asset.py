from django.db import models
from core.types import DomainType


class Asset(models.Model):
    asset_type = models.CharField(
        max_length=20,
        choices=DomainType.choices,
    )
    symbol = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("asset_type", "symbol")

    def __str__(self):
        return f"{self.symbol} ({self.asset_type})"



