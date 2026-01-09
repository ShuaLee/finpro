import logging

from django.db import transaction

from assets.models.asset_core import Asset
from assets.services.syncs.equity import EquitySyncManager
from assets.services.syncs.registry import SYNC_MANAGER_REGISTRY

logger = logging.getLogger(__name__)


class AssetSyncManager:
    """
    Top-level dispatcher that determines which sync manager to use
    based on the asset_type of the Asset.

    Example:
        AssetSyncManager.sync_asset(asset)
    """

    # Map asset_type.slug -> sync manager
    _MANAGERS = SYNC_MANAGER_REGISTRY

    @staticmethod
    @transaction.atomic
    def sync_asset(asset: Asset) -> dict:
        """
        Runs a full sync for a single asset by delegating
        to the correct asset-class-specific sync manager.
        """
        slug = asset.asset_type.slug

        manager_cls = AssetSyncManager._MANAGERS.get(slug)
        if not manager_cls:
            logger.warning(
                f"No sync manager registered for asset type '{slug}'")
            return {"success": False, "reason": "unsupported_asset_type"}

        manager = manager_cls()

        logger.info(f"[SYNC] Starting sync for asset {asset.id} ({slug})")

        result = manager.sync(asset)

        logger.info(f"[SYNC] Completed sync for asset {asset.id} → {result}")

        return {"success": True, "result": result}

    @staticmethod
    def sync_queryset(queryset) -> dict:
        """
        Sync every asset in a queryset (for scheduled tasks).
        Returns aggregated results.
        """
        summary = {"success": 0, "fail": 0}

        for asset in queryset:
            try:
                result = AssetSyncManager.sync_asset(asset)
                if result.get("success"):
                    summary["success"] += 1
                else:
                    summary["fail"] += 1
            except Exception as e:
                logger.exception(
                    f"[SYNC] Failed syncing asset {asset.id}: {e}")
                summary["fail"] += 1

        return summary
