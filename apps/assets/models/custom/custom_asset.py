from django.core.exceptions import ValidationError
from django.db import models

from assets.models.core import Asset
from fx.models.fx import FXCurrency
from users.models import Profile


class CustomAsset(models.Model):
    """
    User-defined asset backed by a core Asset.
    Schema / attributes live elsewhere (SchemaColumnValue).
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

    name = models.CharField(
        max_length=255,
        help_text="User-defined name (e.g. 'Charizard PSA 10').",
    )

    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="custom_assets",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -------------------------
    # Validation
    # -------------------------
    def clean(self):
        super().clean()

        # Admin / service creates Asset later
        if not self.asset_id:
            return

        # Ownership consistency (important)
        if self.asset.owner_id and self.asset.owner_id != self.owner_id:
            raise ValidationError(
                "Asset owner and CustomAsset owner must match."
            )

    def __str__(self):
        return self.name
