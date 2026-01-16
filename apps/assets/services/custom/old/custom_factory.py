from django.db import transaction
from assets.models.core import Asset, AssetType, AssetPrice
from assets.models.custom.custom_asset import CustomAsset


class CustomAssetFactory:

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        owner,
        custom_type,
        name,
        currency,
        attributes=None,
        price=None,
        price_source="MANUAL",
        description="",
    ) -> CustomAsset:

        asset_type = AssetType.objects.get(slug="custom")

        asset = Asset.objects.create(
            asset_type=asset_type,
            currency=currency,
            is_custom=True,
        )

        custom_asset = CustomAsset.objects.create(
            asset=asset,
            owner=owner,
            custom_type=custom_type,
            name=name,
            description=description,
            currency=currency,
            attributes=attributes or {},
        )

        if price is not None:
            AssetPrice.objects.create(
                asset=asset,
                price=price,
                source=price_source,
            )

        return custom_asset
