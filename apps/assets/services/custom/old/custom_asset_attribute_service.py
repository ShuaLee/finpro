from django.core.exceptions import ValidationError

from assets.models.custom import CustomAsset, CustomAssetAttribute, CustomAssetField

from datetime import date
from decimal import Decimal


class CustomAssetAttributeService:

    @staticmethod
    def initialize_attributes(custom_asset: CustomAsset):
        """
        Create empty attribute rows for all fields
        on the asset's schema.
        """
        fields = custom_asset.custom_type.fields.all()

        CustomAssetAttribute.objects.bulk_create([
            CustomAssetAttribute(
                asset=custom_asset,
                field=field,
            )
            for field in fields
        ])

    @staticmethod
    def set_value(
        *,
        asset: CustomAsset,
        field: CustomAssetField,
        value,
    ):
        attr = CustomAssetAttribute.objects.get(
            asset=asset,
            field=field,
        )

        # Clear all values first
        attr.value_text = None
        attr.value_number = None
        attr.value_boolean = None
        attr.value_date = None

        # Type enforcement
        if field.field_type == CustomAssetField.TEXT:
            if not isinstance(value, str):
                raise ValidationError(f"{field.label} must be text")
            attr.value_text = value

        elif field.field_type == CustomAssetField.NUMBER:
            try:
                attr.value_number = Decimal(value)
            except Exception:
                raise ValidationError(f"{field.label} must be a number")

        elif field.field_type == CustomAssetField.BOOLEAN:
            if not isinstance(value, bool):
                raise ValidationError(f"{field.label} must be true/false")
            attr.value_boolean = value

        elif field.field_type == CustomAssetField.DATE:
            if not isinstance(value, date):
                raise ValidationError(f"{field.label} must be a date")
            attr.value_date = value

        elif field.field_type == CustomAssetField.CHOICE:
            if value not in (field.choices or {}):
                raise ValidationError(
                    f"{field.label} must be one of {list(field.choices)}"
                )
            attr.value_text = value

        attr.save()

    @staticmethod
    def set_values(asset: CustomAsset, values: dict):
        for field in asset.custom_type.fields.all():
            if field.name in values:
                CustomAssetAttributeService.set_value(
                    asset=asset,
                    field=field,
                    value=values[field.name],
                )
            elif field.required:
                raise ValidationError(
                    f"Missing required field: {field.label}"
                )
