from django.db import models
from django.core.exceptions import ValidationError

from assets.models.crypto.crypto import CryptoAsset


class CryptoYield(models.Model):
    crypto = models.OneToOneField(
        CryptoAsset,
        on_delete=models.CASCADE,
        related_name="yield_profile",
    )

    annual_yield_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Expected annual yield percentage.",
    )

    notes = models.TextField(blank=True)

    def clean(self):
        if self.annual_yield_percent < 0:
            raise ValidationError("Yield cannot be negative.")
