from django.core.exceptions import ValidationError

from assets.models.core import AssetType


class AssetPolicyService:
    @staticmethod
    def assert_asset_type_usable_by_profile(*, profile, asset_type: AssetType):
        if asset_type.created_by_id is None:
            return

        if asset_type.created_by_id != profile.id:
            raise ValidationError(
                "You cannot use another user's asset type."
            )
