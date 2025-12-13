# assets/models/yields/equity_dividend_event.py

from django.db import models
from django.utils import timezone

from assets.models.asset_core import Asset


class EquityDividendEvent(models.Model):

    class DividendFrequency(models.TextChoices):
        MONTHLY = "Monthly"
        QUARTERLY = "Quarterly"
        SEMI_ANNUAL = "SemiAnnual"
        ANNUAL = "Annual"
        IRREGULAR = "Irregular"
        SPECIAL = "Special"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="dividend_events",
    )

    ex_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    declaration_date = models.DateField(null=True, blank=True)

    amount = models.DecimalField(max_digits=20, decimal_places=6)

    frequency = models.CharField(
        max_length=20,
        choices=DividendFrequency.choices,
    )

    is_special = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ex_date"]
        constraints = [
            # Prevent *true duplicates* but allow multiple events same ex-date
            models.UniqueConstraint(
                fields=["asset", "ex_date", "amount", "payment_date"],
                name="unique_dividend_event",
            )
        ]

    def __str__(self):
        return f"{self.asset} dividend {self.amount} on {self.ex_date}"
