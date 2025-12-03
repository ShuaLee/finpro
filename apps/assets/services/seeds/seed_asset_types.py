from assets.models.assets import AssetType
from core.types import DOMAIN_REGISTRY


def _seed_asset_types():
    """
    Create or update system AssetType rows from DOMAIN_REGISTRY.
    Returns how many were created or updated.
    """
    count = 0

    for domain, meta in DOMAIN_REGISTRY.items():
        label = meta.get("label", domain.replace("_", " ").title())

        _, created = AssetType.objects.update_or_create(
            name=label,
            defaults={
                "domain": domain,
                "is_system": True,
                "created_by": None,
            }
        )

        count += 1  # treat update/create the same

    return count
