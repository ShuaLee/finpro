from django.core.exceptions import ValidationError
from django.db import models

from assets.models.core import Asset
from assets.models.custom.custom_type import CustomAssetType
from fx.models.fx import FXCurrency
from users.models.profile import Profile


class CustomAsset(models.Model):
    """
    User-defined, manually valued asset.

    Represents any real-world asset that does not fit
    into a provider-backed asset class.
    """

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="custom",
    )

    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="custom_assets",
    )

    custom_type = models.ForeignKey(
        CustomAssetType,
        on_delete=models.PROTECT,
        related_name="assets",
    )

    name = models.CharField(
        max_length=255,
        help_text="User-defined asset name (e.g. 'Charizard PSA 10').",
    )

    description = models.TextField(blank=True)

    estimated_value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="User-estimated current value.",
    )

    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
    )

    last_updated = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.asset.asset_type.slug != "custom":
            raise ValidationError(
                "CustomAsset may only attach to assets of type 'custom'."
            )

        if self.custom_type.created_by != self.owner:
            raise ValidationError(
                "You cannot use another user's custom asset type."
            )

    def __str__(self) -> str:
        return f"{self.name} – {self.estimated_value} {self.currency}"
