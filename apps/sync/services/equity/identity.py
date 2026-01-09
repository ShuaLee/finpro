import logging

from assets.models.asset_core import Asset
from external_data.exceptions import ExternalDataError
from sync.services.base import BaseSyncService
from sync.services.equity.profile import EquityProfileSyncService
from sync.services.equity.identity_conflict import (
    EquityIdentityConflictService,
)

logger = logging.getLogger(__name__)


class EquityIdentitySyncService(BaseSyncService):
    """
    Orchestrates equity identity validation and conflict resolution.

    Flow:
    - Run profile sync
    - If identity conflict → resolve + retry on new asset
    """

    name = "equity.identity"

    def _sync(self, asset: Asset) -> dict:
        profile_sync = EquityProfileSyncService(force=self.force)

        try:
            result = profile_sync.sync(asset)
        except ExternalDataError:
            raise

        # -------------------------------
        # No conflict → done
        # -------------------------------
        if result.get("success"):
            return {
                "success": True,
                "asset_id": asset.id,
                "resolved": False,
                "profile": result,
            }

        # -------------------------------
        # Identity conflict → resolve
        # -------------------------------
        if result.get("error") != "identity_conflict":
            return result

        logger.warning(
            "[IDENTITY_SYNC] Conflict detected for asset=%s",
            asset.id,
        )

        resolver = EquityIdentityConflictService()
        new_asset = resolver.resolve(asset)

        # Re-run profile sync on new asset
        retry_result = profile_sync.sync(new_asset)

        return {
            "success": retry_result.get("success", False),
            "resolved": True,
            "old_asset_id": asset.id,
            "new_asset_id": new_asset.id,
            "profile": retry_result,
        }
