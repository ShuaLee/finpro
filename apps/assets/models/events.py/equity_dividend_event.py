from django.db import models

from assets.models.asset_core import Asset

class EquityDividendEvent(models.Model):
    """
    Represents a single dividend declaration or payment.
    Stored as raw events so we can compute trailing 12-month yield,
    handle specials, and analyze history.
    """

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

    is_special = models.BooleanField(
        default=False,
        help_text="Marks this dividend as a non-recurring special dividend."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ex_date"]