import logging
from assets.models.asset import Asset
from assets.services.stock_sync import StockSyncService
from assets.services.crypto_sync import CryptoSyncService
from assets.services.metal_sync import MetalSyncService
from assets.services.bond_sync import BondSyncService
from core.types import DomainType

logger = logging.getLogger(__name__)


# ------------------------------
# Sync Service Registry
# ------------------------------
SYNC_REGISTRY = {
    DomainType.STOCK: StockSyncService,
    DomainType.CRYPTO: CryptoSyncService,
    DomainType.METAL: MetalSyncService,
    DomainType.BOND: BondSyncService, 
    # DomainType.CUSTOM intentionally omitted → skip sync
}


class AssetSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Sync a single asset based on its domain type.
        Returns True if successful, False otherwise.
        """
        if asset.pk is None:
            asset.save()

        service = SYNC_REGISTRY.get(asset.asset_type)
        if not service:
            logger.info(f"No sync service for asset type {asset.asset_type}, skipping")
            return False

        try:
            return service.sync(asset)
        except Exception as e:
            logger.error(f"Error syncing {asset.asset_type} {asset.symbol}: {e}", exc_info=True)
            return False

    @staticmethod
    def sync_many(assets: list[Asset]) -> dict:
        """
        Sync multiple assets.
        Returns a dict with counts of successes and failures.
        """
        results = {"success": 0, "fail": 0}
        for asset in assets:
            if AssetSyncService.sync(asset):
                results["success"] += 1
            else:
                results["fail"] += 1
        return results
