import logging
from typing import Iterable

from django.db import transaction

from assets.models.asset_core import Asset
from sync.services.base import BaseSyncService
from sync.services.equity.identifier import EquityIdentifierSyncService
from sync.services.equity.profile import EquityProfileSyncService
from sync.services.equity.price import EquityPriceSyncService
from sync.services.equity.dividends import EquityDividendSyncService

logger = logging.getLogger(__name__)


class EquitySyncManager(BaseSyncService):
    """
    Orchestrates all equity-related sync services for a single Asset.

    Responsibilities:
    - Define sync ordering
    - Coordinate component execution
    - Aggregate results
    """

    name = "equity.manager"

    COMPONENTS: dict[str, type[BaseSyncService]] = {
        "identifiers": EquityIdentifierSyncService,
        "profile": EquityProfileSyncService,
        "price": EquityPriceSyncService,
        "dividends": EquityDividendSyncService,
    }

    def _sync(
        self,
        asset: Asset,
        *,
        components: Iterable[str] | None = None,
    ) -> dict:
        if asset.asset_type.slug != "equity":
            raise ValueError("EquitySyncManager called for non-equity asset.")

        results: dict[str, dict] = {}

        ordered = self._resolve_components(components)

        logger.info(
            "[EQUITY_SYNC] Starting sync for asset %s (%s)",
            asset.id,
            ordered,
        )

        for name in ordered:
            service_cls = self.COMPONENTS.get(name)
            if not service_cls:
                results[name] = {
                    "success": False,
                    "error": "unknown_component",
                }
                continue

            service = service_cls(force=self.force)

            try:
                logger.info(
                    "[EQUITY_SYNC] Running %s for asset %s",
                    name,
                    asset.id,
                )
                result = service.sync(asset)
                results[name] = result

            except Exception as exc:
                logger.exception(
                    "[EQUITY_SYNC] %s failed for asset %s: %s",
                    name,
                    asset.id,
                    exc,
                )
                results[name] = {
                    "success": False,
                    "error": str(exc),
                }

        logger.info(
            "[EQUITY_SYNC] Completed sync for asset %s",
            asset.id,
        )

        return results

    def _resolve_components(
        self,
        components: Iterable[str] | None,
    ) -> list[str]:
        if components is None:
            ordered = list(self.COMPONENTS.keys())
        else:
            ordered = [c for c in components if c in self.COMPONENTS]

        if "identifiers" in ordered:
            ordered = ["identifiers"] + [
                c for c in ordered if c != "identifiers"
            ]

        return ordered
