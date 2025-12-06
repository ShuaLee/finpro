from django.db import models
from django.core.exceptions import ValidationError

from assets.models.assets import Asset


class CustomDetail(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="custom_detail",
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        # Must be attached to a "custom" asset type
        if self.asset.asset_type.slug != "custom":
            raise ValidationError(
                f"CustomDetail can only attach to assets with type slug='custom', "
                f"but this asset has slug='{self.asset.asset_type.slug}'."
            )

    def __str__(self):
        return self.asset.name
