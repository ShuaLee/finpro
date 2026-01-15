from decimal import Decimal, InvalidOperation
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models

from assets.models.core import Asset
from assets.models.custom.custom_asset_type import CustomAssetType
from assets.models.custom.custom_asset_field import CustomAssetField
from fx.models.fx import FXCurrency
from users.models.profile import Profile


def _validate_decimal(value, label):
    try:
        Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"Field '{label}' must be a decimal number.")


def _validate_boolean(value, label):
    if not isinstance(value, bool):
        raise ValidationError(f"Field '{label}' must be true or false.")


def _validate_date(value, label):
    if isinstance(value, date):
        return

    try:
        date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValidationError(
            f"Field '{label}' must be a valid ISO date (YYYY-MM-DD)."
        )


class CustomAsset(models.Model):
    """
    User-defined, manually valued asset with user-defined structure.
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

    # ✅ User-defined attributes (schema-driven)
    attributes = models.JSONField(
        default=dict,
        help_text="Custom attributes defined by the asset type schema.",
    )

    # ✅ Currency explicitly stored (matches RealEstateAsset)
    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="custom_assets",
        help_text="Currency this asset is valued in.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -------------------------
    # Validation
    # -------------------------
    def clean(self):
        super().clean()

        # ⛔ Asset does not exist yet (admin / factory pre-save)
        if not self.asset_id:
            return

        if self.asset.asset_type.slug != "custom":
            raise ValidationError(
                "CustomAsset may only attach to assets of type 'custom'."
            )

        if self.custom_type.created_by != self.owner:
            raise ValidationError(
                "You cannot use another user's custom asset type."
            )

        schema_fields = {
            f.name: f for f in self.custom_type.fields.all()
        }

        # Required fields
        for field in schema_fields.values():
            if field.required and field.name not in self.attributes:
                raise ValidationError(
                    f"Missing required field: {field.label}"
                )

        # Type validation
        for name, value in self.attributes.items():
            field = schema_fields.get(name)
            if not field:
                raise ValidationError(
                    f"Unknown field '{name}' for asset type '{self.custom_type.name}'."
                )

            label = field.label

            if field.field_type == CustomAssetField.DECIMAL:
                _validate_decimal(value, label)

            elif field.field_type == CustomAssetField.BOOLEAN:
                _validate_boolean(value, label)

            elif field.field_type == CustomAssetField.DATE:
                _validate_date(value, label)

            elif field.field_type == CustomAssetField.CHOICE:
                if not field.choices or value not in field.choices:
                    raise ValidationError(
                        f"Field '{label}' must be one of: {field.choices}"
                    )

            elif field.field_type == CustomAssetField.TEXT:
                if not isinstance(value, str):
                    raise ValidationError(
                        f"Field '{label}' must be text."
                    )

    def __str__(self):
        return self.name
