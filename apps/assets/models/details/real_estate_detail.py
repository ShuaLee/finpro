from django.core.exceptions import ValidationError
from django.db import models

from apps.assets.models.asset_core.asset import Asset
from assets.models import RealEstateType
from fx.models.country import Country


class RealEstateDetail(models.Model):
    """
    Real-estate–specific attributes stored alongside an Asset.
    One-to-one with Asset where asset_type.slug = "real_estate".
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="real_estate_detail",
        limit_choices_to={"asset_type__slug": "real_estate"},
    )

    # --- Location ---
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="real_estate_properties",
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        help_text="State/Province/Region",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City or locality",
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        help_text="Full address (optional)",
    )

    # --- Property Type ---
    property_type = models.ForeignKey(
        RealEstateType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties",
        help_text="Type of property (e.g. Single-Family, Duplex, Commercial).",
    )

    # --- Valuation ---
    purchase_price = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    estimated_value = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    appraisal_date = models.DateField(null=True, blank=True)

    # --- Income/Expenses ---
    rental_income = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    expenses = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    # --- Mortgage ---
    is_mortgaged = models.BooleanField(default=False)
    mortgage_balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True
    )
    monthly_mortgage_payment = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["city"]),
            models.Index(fields=["region"]),
            models.Index(fields=["country"]),
        ]

    # -------------------------------------------------
    # Validation – ensure only real-estate asset types attach
    # -------------------------------------------------
    def clean(self):
        super().clean()

        if self.asset.asset_type.slug != "real_estate":
            raise ValidationError(
                f"RealEstateDetail can only be attached to assets where "
                f"asset_type.slug='real_estate'. Got '{self.asset.asset_type.slug}'."
            )

    def __str__(self):
        name = self.asset.name or "Real Estate"
        loc = ", ".join(
            filter(None, [
                self.city,
                self.region,
                getattr(self.country, "name", None),
            ])
        )
        return f"{name} ({loc})" if loc else name
