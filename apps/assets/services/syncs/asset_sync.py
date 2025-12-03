import logging
from collections import defaultdict

from assets.models.assets import Asset, AssetIdentifier
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


def _display_identifier(asset: Asset) -> str:
    primary_id = asset.identifiers.filter(is_primary=True).first()
    if primary_id:
        return primary_id.value
    if asset.name:
        return asset.name
    return str(asset.id)


class AssetSyncService:
    @staticmethod
    def sync(asset: Asset, profile: bool = False) -> bool:
        domain = asset.asset_type.domain
        service = SYNC_REGISTRY.get(domain)

        if not service:
            logger.info(f"No sync service for {domain}, skipping")
            return False

        try:
            if profile:
                return service.sync_profile(asset)
            return service.sync_quote(asset)
        except Exception as e:
            logger.error(
                f"Error syncing {domain} {_display_identifier(asset)}: {e}",
                exc_info=True,
            )
            return False

    @staticmethod
    def sync_many(assets: list[Asset], profile: bool = False) -> dict:
        results = defaultdict(int)
        grouped = defaultdict(list)

        # group assets by true domain type
        for asset in assets:
            domain = asset.asset_type.domain
            grouped[domain].append(asset)

        for domain, group in grouped.items():
            service = SYNC_REGISTRY.get(domain)

            if not service:
                logger.info(
                    f"No sync service for {domain}, skipping {len(group)} assets"
                )
                results["fail"] += len(group)
                continue

            try:
                bulk_results = {"success": 0, "fail": 0}

                # --- Equities, Crypto, Metals ---
                if domain in {
                    DomainType.EQUITY,
                    DomainType.CRYPTO,
                    DomainType.METAL,
                }:
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

                # --- Bonds ---
                elif domain == DomainType.BOND:
                    if profile:
                        bulk_results = service.sync_profiles_bulk(group)
                    else:
                        bulk_results = service.sync_quotes_bulk(group)

                results["success"] += bulk_results.get("success", 0)
                results["fail"] += bulk_results.get("fail", 0)

            except Exception as e:
                logger.error(
                    f"Bulk sync failed for {domain}: {e}", exc_info=True
                )
                results["fail"] += len(group)

        return dict(results)
