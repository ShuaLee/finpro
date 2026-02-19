from datetime import timedelta

from django.db import models
from django.utils import timezone


class FXCurrency(models.Model):
    """
    Represents a supported currency in the system.
    Populated from FMP forex-list (all traded currencies).
    Example: "USD" → "US Dollar".
    """
    code = models.CharField(
        max_length=3,
        primary_key=True,
        help_text="ISO-like currency code (derived from FX pairs)"
    )
    name = models.CharField(
        max_length=150,
        help_text="Human-readable currency name from FMP"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.name or 'Unknown'})"


class FXRate(models.Model):
    """
    Live FX conversion rate.
    Always stored as FROM → TO.

    Example:
        from_currency = 'USD'
        to_currency = 'CAD'
        rate = 1.3567
        Means 1 USD = 1.3567 CAD.
    """

    from_currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.CASCADE,
        related_name="fx_from_rates",
    )
    to_currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.CASCADE,
        related_name="fx_to_rates",
    )

    rate = models.DecimalField(max_digits=20, decimal_places=10)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_currency", "to_currency"],
                name="unique_fxrate_from_to",
            ),
            models.CheckConstraint(
                condition=~models.Q(from_currency=models.F("to_currency")),
                name="fxrate_from_currency_not_equal_to_to_currency",
            ),
        ]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]
        ordering = ["from_currency__code", "to_currency__code"]

    def __str__(self):
        return f"{self.from_currency.code} → {self.to_currency.code}: {self.rate}"

    def is_stale(self, max_age_hours=24):
        return self.updated_at < timezone.now() - timedelta(hours=max_age_hours)
