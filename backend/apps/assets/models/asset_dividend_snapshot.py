from django.core.exceptions import ValidationError
from django.db import models


class AssetDividendSnapshot(models.Model):
    class CadenceStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        STALE = "stale", "Stale"
        BROKEN = "broken", "Broken"
        NONE = "none", "None"

    class DividendStatus(models.TextChoices):
        CONFIDENT = "confident", "Confident"
        UNCERTAIN = "uncertain", "Uncertain"
        INACTIVE = "inactive", "Inactive"

    asset = models.OneToOneField(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="dividend_snapshot",
    )

    last_dividend_amount = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    last_dividend_date = models.DateField(null=True, blank=True)
    last_dividend_frequency = models.CharField(max_length=30, null=True, blank=True)
    last_dividend_is_special = models.BooleanField(default=False)

    regular_dividend_amount = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    regular_dividend_date = models.DateField(null=True, blank=True)
    regular_dividend_frequency = models.CharField(max_length=30, null=True, blank=True)

    trailing_12m_dividend = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    trailing_12m_cashflow = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    forward_annual_dividend = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    trailing_dividend_yield = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    forward_dividend_yield = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    cadence_status = models.CharField(
        max_length=20,
        choices=CadenceStatus.choices,
        default=CadenceStatus.NONE,
    )
    status = models.CharField(
        max_length=20,
        choices=DividendStatus.choices,
        default=DividendStatus.INACTIVE,
    )

    last_computed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["asset__name"]
        indexes = [
            models.Index(fields=["status", "cadence_status"]),
            models.Index(fields=["last_computed_at"]),
        ]

    def clean(self):
        super().clean()
        if self.asset.asset_type.slug != "equity":
            raise ValidationError("AssetDividendSnapshot may only be attached to equity assets.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dividend snapshot for {self.asset}"
