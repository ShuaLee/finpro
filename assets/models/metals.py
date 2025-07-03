from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal
from accounts.models.metals import StorageFacility
from .base import Asset, AssetHolding


class PreciousMetal(Asset):
    symbol = models.CharField(max_length=10, unqiue=True)
    name = models.CharField(max_length=50)
    price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    currency = models.CharField(
        max_length=3,
        choices=settings.CURRENCY_CHOICES,
        blank=True,
        null=True
    )
    is_custom = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["symbol"]),
            models.Index(fields=["is_custom"]),
        ]

    def __str__(self):
        return self.symbol

    def save(self, *args, **kwargs):
        if self.symbol:
            self.symbol = self.symbol.upper()
        super().save(*args, **kwargs)

    def get_price(self):
        return self.price or Decimal("0")


class PreciousMetalHolding(AssetHolding):
    storage_facility = models.ForeignKey(
        StorageFacility,
        on_delete=models.CASCADE,
        related_name='holdings'
    )
    precious_metal = models.ForeignKey(
        PreciousMetal,
        on_delete=models.CASCADE,
        related_name='precious_metal_holdings'
    )

    @property
    def asset(self):
        return self.precious_metal

    def __str__(self):
        return f"{self.precious_metal} ({self.quantity} oz)"

    def get_asset_type(self):
        return 'metal'

    def get_active_schema(self):
        return self.storage_facility.metal_portfolio.active_schema

    def get_column_model(self):
        from schemas.models.metals import MetalPortfolioSC
        return MetalPortfolioSC

    def get_column_value_model(self):
        from schemas.models.metals import MetalPortfolioSCV
        return MetalPortfolioSCV

    def get_profile_currency(self):
        return self.storage_facility.metal_portfolio.portfolio.profile.currency

    class Meta:
        indexes = [
            models.Index(fields=["storage_facility"]),
            models.Index(fields=["precious_metal"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["storage_facility", "precious_metal"],
                name="unique_precious_metal_per_storage"
            )
        ]
