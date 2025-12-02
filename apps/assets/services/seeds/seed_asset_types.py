from assets.models.assets import AssetType
from core.types import DOMAIN_REGISTRY


def _seed_asset_types(self):
    """
    Create system AssetType rows from DOMAIN_REGISTRY.
    """

    for domain, meta in DOMAIN_REGISTRY.items():
        label = meta.get("label", domain.replace("_", " ").title())

        AssetType.objects.update_or_create(
            name=label,
            defaults={
                "domain": domain,
                "is_system": True,
                "created_by": None,
            }
        )
