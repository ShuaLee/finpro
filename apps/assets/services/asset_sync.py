import logging
from assets.models.asset import Asset
from apps.assets.services.equity_sync import EquitySyncService
from assets.services.crypto_sync import CryptoSyncService
from assets.services.metal_sync import MetalSyncService
from assets.services.bond_sync import BondSyncService
from core.types import DomainType
from apps.external_data.fmp.dispatch import detect_asset_type

logger = logging.getLogger(__name__)

# ------------------------------
# Sync Service Registry
# ------------------------------
SYNC_REGISTRY = {
    DomainType.EQUITY: EquitySyncService,
    DomainType.CRYPTO: CryptoSyncService,
    DomainType.METAL: MetalSyncService,
    DomainType.BOND: BondSyncService,
    # DomainType.CUSTOM and DomainType.REAL_ESTATE intentionally omitted → skip sync
}


class AssetSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Sync a single asset based on its domain type.
        Validates that the symbol actually belongs to that domain.
        Returns True if successful, False otherwise.
        """
        if asset.pk is None:
            asset.save()

        # ✅ Step 1: Detect true type
        detected_type = detect_asset_type(asset.symbol)
        if detected_type and detected_type != asset.asset_type:
            logger.warning(
                f"Type mismatch for {asset.symbol}: "
                f"expected={asset.asset_type}, detected={detected_type}"
            )
            return False

        # ✅ Step 2: Get sync service
        service = SYNC_REGISTRY.get(asset.asset_type)
        if not service:
            logger.info(
                f"No sync service for asset type {asset.asset_type}, skipping")
            return False

        # ✅ Step 3: Execute sync
        try:
            return service.sync(asset)
        except Exception as e:
            logger.error(
                f"Error syncing {asset.asset_type} {asset.symbol}: {e}",
                exc_info=True,
            )
            return False

    @staticmethod
    def sync_many(assets: list[Asset], mode: str = "quotes") -> dict:
        """
        Sync multiple assets efficiently.
        For equities: batch sync using bulk API.
        For others: fallback to per-asset sync.

        mode: "profiles" (daily full update) or "quotes" (intraday price update)
        """
        results = {"success": 0, "fail": 0}

        # ✅ Group assets by type
        equities = [a for a in assets if a.asset_type == DomainType.EQUITY]
        others = [a for a in assets if a.asset_type != DomainType.EQUITY]

        # ------------------------------
        # Equities (bulk sync)
        # ------------------------------
        if equities:
            symbols = [a.symbol for a in equities if a.symbol]
            if mode == "profiles":
                count = EquitySyncService.sync_profiles_bulk(symbols)
                results["success"] += count
                results["fail"] += len(symbols) - count
            else:  # default to quotes
                count = EquitySyncService.sync_quotes_bulk(symbols)
                results["success"] += count
                results["fail"] += len(symbols) - count

        # ------------------------------
        # Other asset types (loop)
        # ------------------------------
        for asset in others:
            if AssetSyncService.sync(asset):
                results["success"] += 1
            else:
                results["fail"] += 1

        return results
