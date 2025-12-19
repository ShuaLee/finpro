from django.db import models

from assets.models.asset_core import Asset


class EquityDividendExtension(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="dividend_extension",
    )

    trailing_dividend_12m = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )

    forward_dividend = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )

    last_computed = models.DateTimeField(auto_now=True)
