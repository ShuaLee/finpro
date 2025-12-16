from accounts.config.account_types import SYSTEM_ACCOUNT_TYPES
from accounts.models.account_type import AccountType
from assets.models.asset_core import AssetType
from django.core.exceptions import ImproperlyConfigured


def seed_account_types():
    """
    Create or update system AccountTypes and assign M2M asset types.
    Fully safe, explicit, and validates asset type slugs.
    """
    count = 0

    for cfg in SYSTEM_ACCOUNT_TYPES:
        slug = cfg["slug"]
        allowed_slugs = cfg.get("allowed_asset_types", [])

        # Create or update the AccountType row
        account_type, _ = AccountType.objects.update_or_create(
            slug=slug,
            defaults={
                "name": cfg["name"],
                "allows_multiple": cfg["allows_multiple"],
                "is_system": True,
                "description": cfg.get("description", None),
            },
        )

        # --- Validate that all provided slugs exist ---
        db_asset_types = list(AssetType.objects.filter(slug__in=allowed_slugs))
        db_slugs = {a.slug for a in db_asset_types}

        missing = set(allowed_slugs) - db_slugs
        if missing:
            raise ImproperlyConfigured(
                f"AssetType slug(s) not found for AccountType '{slug}': {missing}"
            )

        # Assign M2M asset types
        account_type.allowed_asset_types.set(db_asset_types)

        count += 1

    return count
