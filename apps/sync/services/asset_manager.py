import logging

from django.db import transaction

from assets.models.asset_core import Asset
from sync.services.registry import SYNC_MANAGER_REGISTRY

logger = logging.getLogger(__name__)


class AssetSyncManager:
    """
    Top-level dispatcher that determines which sync manager to use
    based on the asset_type of the Asset.

    This is the SINGLE public entry point for all asset syncs.
    """

    @staticmethod
    @transaction.atomic
    def sync_asset(asset: Asset, *, force: bool = False) -> dict:
        """
        Run a full sync for a single asset.

        This method is safe to call from:
        - management commands
        - admin actions
        - scheduled jobs
        """
        slug = asset.asset_type.slug

        manager_cls = SYNC_MANAGER_REGISTRY.get(slug)
        if not manager_cls:
            logger.warning(
                "No sync manager registered for asset type '%s'", slug
            )
            return {
                "success": False,
                "error": "unsupported_asset_type",
            }

        manager = manager_cls(force=force)

        logger.info(
            "[SYNC] Starting %s sync for asset %s",
            slug,
            asset.id,
        )

        try:
            result = manager.sync(asset)
        except Exception as exc:
            logger.exception(
                "[SYNC] Failed syncing asset %s (%s): %s",
                asset.id,
                slug,
                exc,
            )
            return {
                "success": False,
                "error": str(exc),
            }

        logger.info(
            "[SYNC] Completed %s sync for asset %s",
            slug,
            asset.id,
        )

        return {
            "success": True,
            "result": result,
        }
