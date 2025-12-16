from assets.config.asset_types import SYSTEM_ASSET_TYPES
from assets.models.asset_core import AssetType


def seed_asset_types():
    count = 0

    for data in SYSTEM_ASSET_TYPES:
        _, created = AssetType.objects.update_or_create(
            slug=data["slug"],
            defaults={
                "name": data["name"],
                "identifier_rules": data["identifier_rules"],
                "is_system": True,
                "created_by": None,
            },
        )
        count += 1

    return count
