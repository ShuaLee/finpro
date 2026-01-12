from django.db import transaction

from assets.models.core import AssetType

SYSTEM_ASSET_TYPES = [
    ("equity", "Equity"),
    ("crypto", "Cryptocurrency"),
    ("commodity", "Commodity"),
    ("real_estate", "Real Estate"),
    ("custom", "Custom Asset"),
]


class AssetTypeSeeder:
    """
    Seeds required system AssetTypes.
    Safe to run multiple times.
    """

    @classmethod
    @transaction.atomic
    def run(cls) -> None:
        for slug, name in SYSTEM_ASSET_TYPES:
            AssetType.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )
