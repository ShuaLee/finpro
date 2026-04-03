from django.core.exceptions import ValidationError

from apps.assets.models import AssetType


class AssetTypeService:
    @staticmethod
    def list_available_for_profile(*, profile):
        return AssetType.objects.filter(created_by__isnull=True) | AssetType.objects.filter(
            created_by=profile
        )

    @staticmethod
    def create_custom_asset_type(
        *,
        profile,
        name: str,
        description: str = "",
    ) -> AssetType:
        asset_type = AssetType(
            name=(name or "").strip(),
            created_by=profile,
            description=(description or "").strip(),
        )
        asset_type.save()
        return asset_type

    @staticmethod
    def update_custom_asset_type(
        *,
        asset_type: AssetType,
        profile,
        name: str | None = None,
        description: str | None = None,
    ) -> AssetType:
        if asset_type.is_system:
            raise ValidationError("System asset types cannot be edited.")
        if asset_type.created_by != profile:
            raise ValidationError("You cannot edit another user's asset type.")

        if name is not None:
            asset_type.name = name
        if description is not None:
            asset_type.description = description

        asset_type.save()
        return asset_type

    @staticmethod
    def delete_custom_asset_type(*, asset_type: AssetType, profile) -> None:
        if asset_type.is_system:
            raise ValidationError("System asset types cannot be deleted.")
        if asset_type.created_by != profile:
            raise ValidationError("You cannot delete another user's asset type.")
        asset_type.delete()
