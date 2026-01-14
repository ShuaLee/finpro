from django.db import models
from django.core.exceptions import ValidationError

from assets.models.core import Asset


class EquityDividendSnapshot(models.Model):
    """
    Dividend snapshot for an equity asset.

    Stores:
    - What actually happened (last dividend)
    - What appears to be regular (anchor dividend)
    - What was paid in the trailing window (facts)
    - What we estimate forward (heuristic)
    - How confident we are in the cadence
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="equity_dividend",
    )

    # =================================================
    # LAST ACTUAL DIVIDEND (FACT)
    # =================================================
    last_dividend_amount = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Amount of the most recent dividend paid (per share).",
    )

    last_dividend_date = models.DateField(
        null=True,
        blank=True,
        help_text="Ex-dividend date of the most recent dividend.",
    )

    last_dividend_frequency = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        help_text="Raw provider frequency for the most recent dividend.",
    )

    last_dividend_is_special = models.BooleanField(
        default=False,
        help_text="True if the most recent dividend was special or irregular.",
    )

    # =================================================
    # REGULAR DIVIDEND ANCHOR (INFERENCE)
    # =================================================
    regular_dividend_amount = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Most recent non-special dividend amount.",
    )

    regular_dividend_date = models.DateField(
        null=True,
        blank=True,
        help_text="Ex-dividend date of the most recent non-special dividend.",
    )

    regular_dividend_frequency = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        help_text="Inferred regular dividend frequency (e.g. Quarterly).",
    )

    # =================================================
    # TRAILING (FACTUAL, NON-INFERRED)
    # =================================================
    trailing_12m_dividend = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        default=0,
        help_text="Sum of regular (non-special) dividends in the last 12 months.",
    )

    trailing_12m_cashflow = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        default=0,
        help_text="Total dividends paid in the last 12 months (incl. specials).",
    )

    # =================================================
    # FORWARD (HEURISTIC ESTIMATE)
    # =================================================
    forward_annual_dividend = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Estimated annual dividend based on regular dividend cadence.",
    )

    # =================================================
    # CADENCE HEALTH (NEW — IMPORTANT)
    # =================================================
    class DividendCadenceStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        STALE = "STALE", "Stale"
        BROKEN = "BROKEN", "Broken"
        NONE = "NONE", "None"

    cadence_status = models.CharField(
        max_length=20,
        choices=DividendCadenceStatus.choices,
        default=DividendCadenceStatus.NONE,
        help_text="Health of the inferred regular dividend cadence.",
    )

    # =================================================
    # CONFIDENCE / VALUATION STATUS
    # =================================================
    class DividendStatus(models.TextChoices):
        CONFIDENT = "CONFIDENT", "Confident"
        UNCERTAIN = "UNCERTAIN", "Uncertain"
        INACTIVE = "INACTIVE", "Inactive"

    status = models.CharField(
        max_length=20,
        choices=DividendStatus.choices,
        default=DividendStatus.INACTIVE,
        help_text="Confidence in dividend forward estimates.",
    )

    last_computed = models.DateTimeField(
        auto_now=True,
        help_text="Last time the dividend snapshot was recomputed.",
    )

    # =================================================
    # VALIDATION
    # =================================================
    def clean(self):
        if self.asset.asset_type.slug != "equity":
            raise ValidationError(
                "EquityDividendSnapshot may only be attached to equity assets."
            )

    def __str__(self):
        return f"Dividend snapshot for {self.asset}"
