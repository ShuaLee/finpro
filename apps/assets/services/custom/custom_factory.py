from django.db import transaction

from assets.models.custom import CustomAsset, CustomAssetType
from assets.services.base import BaseAssetFactory
from fx.models.fx import FXCurrency
from users.models.profile import Profile


class CustomAssetFactory(BaseAssetFactory):
    asset_type_slug = "custom"

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        owner: Profile,
        custom_type: CustomAssetType,
        name: str,
        estimated_value,
        currency: FXCurrency,
        description: str = "",
    ) -> CustomAsset:
        asset = cls._create_asset()

        return CustomAsset.objects.create(
            asset=asset,
            owner=owner,
            custom_type=custom_type,
            name=name,
            description=description,
            estimated_value=estimated_value,
            currency=currency,
        )
