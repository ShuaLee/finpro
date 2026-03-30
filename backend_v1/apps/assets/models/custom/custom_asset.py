from django.core.exceptions import ValidationError
from django.db import models, transaction

from assets.models.core import Asset
from assets.services.policy import AssetPolicyService
from fx.models.fx import FXCurrency
from profiles.models import Profile


class CustomAsset(models.Model):
    """
    User-defined asset backed by a core Asset.
    Schema / attributes live elsewhere (SchemaColumnValue).
    """

    class Reason(models.TextChoices):
        USER = "user", "User created"
        MARKET = "market", "Market removed"

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

    reason = models.CharField(
        max_length=20,
        choices=Reason.choices,
    )

    requires_review = models.BooleanField(
        default=False,
        help_text="Indicates this asset was auto-created due to a market change and requires user review."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    frozen_at = models.DateTimeField(null=True, blank=True)

    # -------------------------
    # Validation
    # -------------------------
    def clean(self):
        super().clean()

        # Admin / service creates Asset later
        if not self.asset_id or not self.owner_id:
            return

        AssetPolicyService.assert_asset_type_usable_by_profile(
            profile=self.owner,
            asset_type=self.asset.asset_type,
        )

        # Avoid duplicate custom labels under same owner + asset type.
        duplicate_exists = CustomAsset.objects.filter(
            owner=self.owner,
            asset__asset_type=self.asset.asset_type,
            name__iexact=self.name,
        ).exclude(pk=self.pk).exists()
        if duplicate_exists:
            raise ValidationError(
                "You already have a custom asset with this name for that asset type."
            )

        if self.pk:
            original = CustomAsset.objects.only("asset_id", "owner_id").filter(pk=self.pk).first()
            if original and original.asset_id != self.asset_id:
                raise ValidationError("Custom asset link cannot be changed.")
            if original and original.owner_id != self.owner_id:
                raise ValidationError("Custom asset owner cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        asset = self.asset
        with transaction.atomic():
            super().delete(*args, **kwargs)
            asset.delete()

    def __str__(self):
        return self.name
