from django.db import models

from assets.models.asset_core import Asset


class EquityDividendEvent(models.Model):
    """
    Represents a single historical dividend event for an equity asset.

    This model stores raw, factual dividend data as reported by external
    providers (e.g. FMP). No assumptions are made about recurrence,
    special classification, or forward-looking behavior at the model level.

    Design principles:
    - One row == one dividend event
    - Events are uniquely identified by (asset, ex_date)
    - Trailing dividends are computed by summing events over time windows
    - Forward dividends are derived later using frequency heuristics
    - Raw provider frequency strings are preserved for flexibility

    Any classification such as "special dividend" or cadence normalization
    should be derived from historical patterns, not hardcoded here.
    """

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="dividend_events",
    )

    # --- Key Dates ---
    ex_date = models.DateField()
    record_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    declaration_date = models.DateField(null=True, blank=True)

    # --- Dividend Amounts ---
    dividend = models.DecimalField(max_digits=20, decimal_places=6)
    adj_dividend = models.DecimalField(
        max_digits=20, decimal_places=6,
        null=True,
        blank=True,
        help_text="Split-adjusted dividend as reported by provider"
    )

    # --- Provider Metadata ---
    yield_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Yield value as reported by provider (not used for calculations)"
    )

    frequency = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Raw dividend frequency string as returned by provider"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ex_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["asset", "ex_date"],
                name="uniq_equity_dividend_event"
            )
        ]
        indexes = [
            models.Index(fields=["asset", "ex_date"]),
        ]

    def __str__(self):
        return f"{self.asset} dividend {self.dividend} on {self.ex_date}"
