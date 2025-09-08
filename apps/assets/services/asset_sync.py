import logging
from assets.models.asset import Asset, AssetType
from assets.services.stock_sync import StockSyncService
from assets.services.crypto_sync import CryptoSyncService
from assets.services.metal_sync import MetalSyncService

logger = logging.getLogger(__name__)


class AssetSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Sync a single asset based on its asset_type.
        Returns True if successful, False otherwise.
        """
        if asset.pk is None:
            asset.save()

        if asset.asset_type == AssetType.STOCK:
            return StockSyncService.sync(asset)

        elif asset.asset_type == AssetType.CRYPTO:
            return CryptoSyncService.sync(asset)

        elif asset.asset_type == AssetType.METAL:
            return MetalSyncService.sync(asset)

        elif asset.asset_type == AssetType.CUSTOM:
            logger.info(f"Skipping sync for custom asset {asset.symbol}")
            return False

        else:
            logger.warning(f"Unsupported asset type: {asset.asset_type}")
            return False

    @staticmethod
    def sync_many(assets: list[Asset]) -> dict:
        """
        Sync multiple assets.
        Returns a dict with counts of successes and failures.
        """
        results = {"success": 0, "fail": 0}
        for asset in assets:
            ok = AssetSyncService.sync(asset)
            if ok:
                results["success"] += 1
            else:
                results["fail"] += 1
        return results
