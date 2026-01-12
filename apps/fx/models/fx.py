from django.db import models, transaction
from django.utils import timezone

from datetime import timedelta


class FXCurrency(models.Model):
    """
    Represents a supported currency in the system.
    Populated from FMP forex-list (all traded currencies).
    Example: "USD" → "US Dollar".
    """
    code = models.CharField(
        max_length=6,
        primary_key=True,
        help_text="ISO-like currency code (derived from FX pairs)"
    )
    name = models.CharField(
        max_length=150,
        help_text="Human-readable currency name from FMP"
    )

    created_at = models.DateTimeField(auto_now_add=True)

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
        unique_together = [("from_currency", "to_currency")]
        ordering = ["from_currency__code", "to_currency__code"]

    def __str__(self):
        return f"{self.from_currency.code} → {self.to_currency.code}: {self.rate}"

    # ---------------------------
    # Helpers
    # ---------------------------

    def is_stale(self, max_age_hours=24):
        return self.updated_at < timezone.now() - timedelta(hours=max_age_hours)

    # ---------------------------
    # FX-dependent recalculation
    # ---------------------------

    def save(self, *args, **kwargs):
        """
        Save the FX rate and trigger recalculation of SCVs
        that depend on FX (current_value_profile_fx).
        """

        super().save(*args, **kwargs)

        # We delay recalculation until transaction commits
        def _after_commit():
            from schemas.services.recalc_triggers import recalc_holdings_for_fx_pair
            recalc_holdings_for_fx_pair(
                self.from_currency.code,
                self.to_currency.code
            )

        transaction.on_commit(_after_commit)
