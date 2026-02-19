from assets.models.core import Asset
from assets.models.core import AssetType


class BaseAssetFactory:
    asset_type_slug: str

    @classmethod
    def _create_asset(cls) -> Asset:
        asset_type = AssetType.objects.get(slug=cls.asset_type_slug)
        return Asset.objects.create(asset_type=asset_type)
