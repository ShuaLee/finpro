from django.db import models
from portfolios.models.metals import MetalPortfolio
from .base import BaseAccount

class StorageFacility(BaseAccount):
    metals_portfolio = models.ForeignKey(
        MetalPortfolio,
        on_delete=models.CASCADE,
        related_name='storage_facilities'
    )
    is_lending_account = models.BooleanField(default=False)
    is_insured = models.BooleanField(default=False)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)