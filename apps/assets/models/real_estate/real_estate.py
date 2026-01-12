from django.db import models
from django.core.exceptions import ValidationError

from assets.models.core import Asset
from assets.models.real_estate import RealEstateType
from fx.models.fx import FXCurrency
from fx.models.country import Country
from users.models import Profile


class RealEstateAsset(models.Model):
    """
    Represents a real estate holding.

    - User-owned
    - Manually valued
    - No external pricing source
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="real_estate",
    )

    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="real_estate_assets",
    )

    property_type = models.ForeignKey(
        RealEstateType,
        on_delete=models.PROTECT,
        related_name="properties",
    )

    # -------------------------
    # Location
    # -------------------------
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="real_estate_assets",
    )

    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    # -------------------------
    # Valuation
    # -------------------------
    estimated_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="User-estimated current value.",
    )

    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="real_estate_assets",
    )

    last_updated = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True)

    # -------------------------
    # Validation
    # -------------------------
    def clean(self):
        if self.asset.asset_type.slug != "real_estate":
            raise ValidationError(
                "RealEstateAsset may only attach to real_estate assets."
            )

        # Enforce ownership on user-defined types
        if self.property_type.created_by and self.property_type.created_by != self.owner:
            raise ValidationError(
                "You cannot use another user's custom property type."
            )

    def __str__(self):
        return f"{self.property_type} – {self.estimated_value} {self.currency}"
