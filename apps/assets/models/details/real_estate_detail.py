from django.db import models
from assets.models.assets import Asset
from core.types import DomainType


class RealEstateDetail(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="real_estate_detail",
        limit_choices_to={"asset_type": DomainType.REAL_ESTATE},
    )

    # --- Core Info ---
    location = models.CharField(
        max_length=255,
        help_text="City/region or address"
    )
    property_type = models.CharField(
        max_length=100,
        help_text="e.g., Residential, Commercial, Land, Mixed-use"
    )
    currency = models.CharField(max_length=10, default="USD")

    # --- Valuation ---
    purchase_price = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        help_text="Price originally paid"
    )
    estimated_value = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        help_text="Latest estimated market value"
    )
    appraisal_date = models.DateField(
        null=True, blank=True,
        help_text="Date of last valuation/appraisal"
    )

    # --- Income/Expenses ---
    rental_income = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        help_text="Monthly or annual rental income"
    )
    expenses = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        help_text="Annual expenses (taxes, maintenance, insurance, etc.)"
    )
    mortgage_balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        help_text="Outstanding mortgage balance if applicable"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["location"]),
            models.Index(fields=["property_type"]),
        ]

    def __str__(self):
        return f"{self.asset.symbol} ({self.location})"
