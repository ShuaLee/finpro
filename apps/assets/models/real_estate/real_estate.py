from django.db import models, transaction
from django.core.exceptions import ValidationError

from assets.models.core import Asset, AssetType
from assets.models.real_estate.real_estate_type import RealEstateType
from fx.models.fx import FXCurrency
from fx.models.country import Country
from users.models import Profile


class RealEstateAsset(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="real_estate",
        editable=False,
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

    is_owner_occupied = models.BooleanField(default=False)

    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="real_estate_assets",
    )

    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="real_estate_assets",
    )

    notes = models.TextField(blank=True)

    # -------------------------------------------------
    # Lifecycle
    # -------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.asset_id:
            with transaction.atomic():
                asset_type = AssetType.objects.get(slug="real_estate")
                asset = Asset.objects.create(asset_type=asset_type)
                self.asset = asset

        super().save(*args, **kwargs)

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    def clean(self):
        # asset may not exist yet during admin add
        if self.asset_id:
            if self.asset.asset_type.slug != "real_estate":
                raise ValidationError(
                    "RealEstateAsset may only attach to real_estate assets."
                )

        if self.property_type.created_by and self.property_type.created_by != self.owner:
            raise ValidationError(
                "You cannot use another user's custom property type."
            )

    def __str__(self):
        return f"{self.property_type} – {self.city or '—'}"
