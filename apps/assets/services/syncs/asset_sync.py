import logging
from collections import defaultdict

from assets.models.assets import Asset, AssetIdentifier

# Sync services
from assets.services.syncs.equity_sync import EquitySyncService
from assets.services.syncs.crypto_sync import CryptoSyncService
from assets.services.syncs.metal_sync import MetalSyncService
from assets.services.syncs.bond_sync import BondSyncService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# SYNC REGISTRY — keyed by AssetType.slug
# ---------------------------------------------------------
SYNC_REGISTRY = {
    "equity": EquitySyncService,
    "crypto": CryptoSyncService,
    "metal": MetalSyncService,
    "bond": BondSyncService,
    # No sync for custom or real_estate
}


def _display_identifier(asset: Asset) -> str:
    """Pretty-print asset using primary identifier or name."""
    primary = asset.identifiers.filter(is_primary=True).first()
    if primary:
        return primary.value
    if asset.name:
        return asset.name
    return str(asset.id)


class AssetSyncService:
    """
    Routes assets to the correct sync handler based on their AssetType.slug.
    """

    @staticmethod
    def sync(asset: Asset, profile: bool = False) -> bool:
        slug = asset.asset_type.slug
        service = SYNC_REGISTRY.get(slug)

        if not service:
            logger.info(f"No sync service for asset type '{slug}', skipping.")
            return False

        try:
            if profile:
                return service.sync_profile(asset)
            return service.sync_quote(asset)

        except Exception as e:
            logger.error(
                f"Error syncing '{slug}' for {_display_identifier(asset)}: {e}",
                exc_info=True,
            )
            return False

    @staticmethod
    def sync_many(assets: list[Asset], profile: bool = False) -> dict:
        """
        Bulk-sync assets grouped by their AssetType.slug.
        Returns { "success": X, "fail": Y }.
        """
        results = defaultdict(int)
        grouped = defaultdict(list)

        # Group by slug
        for asset in assets:
            slug = asset.asset_type.slug
            grouped[slug].append(asset)

        # Process each slug group
        for slug, group in grouped.items():
            service = SYNC_REGISTRY.get(slug)

            if not service:
                logger.info(
                    f"No sync service for '{slug}', skipping {len(group)} assets.")
                results["fail"] += len(group)
                continue

            try:
                bulk = {"success": 0, "fail": 0}

                # Preferred bulk APIs if available
                if profile and hasattr(service, "sync_profiles_bulk"):
                    bulk = service.sync_profiles_bulk(group)

                elif not profile and hasattr(service, "sync_quotes_bulk"):
                    bulk = service.sync_quotes_bulk(group)

                else:
                    # Fall back to per-asset sync
                    for asset in group:
                        if AssetSyncService.sync(asset, profile=profile):
                            bulk["success"] += 1
                        else:
                            bulk["fail"] += 1

                results["success"] += bulk.get("success", 0)
                results["fail"] += bulk.get("fail", 0)

            except Exception as e:
                logger.error(
                    f"Bulk sync failed for slug '{slug}': {e}", exc_info=True)
                results["fail"] += len(group)

        return dict(results)
