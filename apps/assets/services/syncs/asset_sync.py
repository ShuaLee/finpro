import logging
from collections import defaultdict
from assets.models.asset import Asset
from core.types import DomainType

from assets.services.syncs.equity_sync import EquitySyncService
from assets.services.syncs.crypto_sync import CryptoSyncService
from assets.services.syncs.metal_sync import MetalSyncService
from assets.services.syncs.bond_sync import BondSyncService

logger = logging.getLogger(__name__)


SYNC_REGISTRY = {
    DomainType.EQUITY: EquitySyncService,
    DomainType.CRYPTO: CryptoSyncService,
    DomainType.METAL: MetalSyncService,
    DomainType.BOND: BondSyncService,
    # CUSTOM, REAL_ESTATE intentionally excluded
}


class AssetSyncService:
    @staticmethod
    def sync(asset: Asset, profile: bool = False) -> bool:
        """
        Sync a single asset.
        profile=True → sync long-lived metadata
        profile=False → sync price/quote
        """
        service = SYNC_REGISTRY.get(asset.asset_type)
        if not service:
            logger.info(f"No sync service for {asset.asset_type}, skipping")
            return False

        try:
            if profile:
                return service.sync_profile(asset)
            return service.sync_quote(asset)
        except Exception as e:
            logger.error(
                f"Error syncing {asset.asset_type} {asset.symbol}: {e}", exc_info=True)
            return False

    @staticmethod
    def sync_many(assets: list[Asset], profile: bool = False) -> dict:
        """
        Sync many assets efficiently by grouping by type.
        Uses bulk APIs when possible (equities, crypto, metals for profiles & quotes;
        bonds only for quotes).
        """
        results = defaultdict(int)
        grouped = defaultdict(list)

        # group by asset type
        for asset in assets:
            grouped[asset.asset_type].append(asset)

        for asset_type, group in grouped.items():
            service = SYNC_REGISTRY.get(asset_type)
            if not service:
                logger.info(
                    f"No sync service for {asset_type}, skipping {len(group)} assets")
                results["fail"] += len(group)
                continue

            try:
                bulk_results = {"success": 0, "fail": 0}

                # --- Equities, Crypto, Metals: bulk supported for both profile & quote ---
                if asset_type in {DomainType.EQUITY, DomainType.CRYPTO, DomainType.METAL}:
                    if profile and hasattr(service, "sync_profiles_bulk"):
                        bulk_results = service.sync_profiles_bulk(group)
                    elif not profile and hasattr(service, "sync_quotes_bulk"):
                        bulk_results = service.sync_quotes_bulk(group)
                    else:
                        for asset in group:
                            if AssetSyncService.sync(asset, profile=profile):
                                bulk_results["success"] += 1
                            else:
                                bulk_results["fail"] += 1

                # --- Bonds: only bulk quotes, profiles must loop ---
                elif asset_type == DomainType.BOND:
                    if profile:
                        bulk_results = service.sync_profiles_bulk(
                            group)  # loops internally
                    else:
                        bulk_results = service.sync_quotes_bulk(group)

                results["success"] += bulk_results.get("success", 0)
                results["fail"] += bulk_results.get("fail", 0)

            except Exception as e:
                logger.error(
                    f"Bulk sync failed for {asset_type}: {e}", exc_info=True)
                results["fail"] += len(group)

        return dict(results)
