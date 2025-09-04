from django.db import models
from portfolios.models.metal import MetalPortfolio
from .base import BaseAccount


class MetalAccount(BaseAccount):
    metal_portfolio = models.ForeignKey(
        MetalPortfolio,
        on_delete=models.CASCADE,
        related_name='storage_facilities'
    )

    asset_type = "metal"
    account_variant = "storage_facility"

    class Meta:
        verbose_name = "Storage Facility"
        constraints = [
            models.UniqueConstraint(
                fields=['metal_portfolio', 'name'],
                name='unique_storagefacility_name_in_portfolio'
            )
        ]

    @property
    def sub_portfolio(self):
        return self.metal_portfolio

    @property
    def active_schema(self):
        return self.metal_portfolio.get_schema_for_account_model("storage_facility")
