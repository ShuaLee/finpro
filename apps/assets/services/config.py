from assets.config import ASSET_SCHEMA_CONFIG
from assets.models import AssetSchemaConfig  # For dynamic configs


def get_asset_schema_config(asset_type):
    """
    Returns schema config for a given asset type.
    Checks DB for custom configs before falling back to static.
    """
    custom = AssetSchemaConfig.objects.filter(asset_type=asset_type).first()
    if custom:
        return custom.config

    return ASSET_SCHEMA_CONFIG.get(asset_type, {})
