import logging

from django.db import transaction

from assets.models.asset_core import Asset
from assets.services.syncs.equity import (
    EquityIdentifierSyncService,
    EquityProfileSyncService,
    EquityPriceSyncService,
    EquityDividendSyncService,
)

logger = logging.getLogger(__name__)


class EquitySyncManager:
    """
    The single entrypoint for refreshing all data for one equity.

    Runs syncs in correct dependency order:

        1. Identifiers
        2. Profile
        3. Price
        4. Dividends

    Produces a structured results dict used by API views,
    admin commands, nightly jobs, & debugging interfaces.
    """

    @staticmethod
    @transaction.atomic
    def sync(asset: Asset) -> dict:
        if asset.asset_type.slug != "equity":
            raise ValueError(
                f"EquityAssetSyncOrchestrator called on non-equity asset {asset.id}"
            )

        results = {}

        try:
            # 1. IDENTIFIERS — must run first
            results["identifiers"] = EquityIdentifierSyncService().sync(asset)

            # 2. PROFILE — depends on knowing correct ticker
            results["profile"] = EquityProfileSyncService.sync(asset)

            # 3. PRICE — requires valid profile + currency
            results["price"] = EquityPriceSyncService.sync(asset)

            # 4. DIVIDENDS — depends on ticker + profile
            results["dividends"] = EquityDividendSyncService.sync(asset)

        except Exception as e:
            logger.error(
                f"[EQUITY_ORCHESTRATOR] Sync failed for asset {asset.id}: {e}",
                exc_info=True
            )
            results["error"] = str(e)

        return results
