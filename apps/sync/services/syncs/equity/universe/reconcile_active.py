import logging

from django.db import transaction

from assets.models.asset_core import AssetIdentifier
from assets.models.profiles.equity_profile import EquityProfile
from external_data.providers.fmp.client import FMP_PROVIDER
from sync.services.syncs.base import BaseSyncService

logger = logging.getLogger(__name__)


class ReconcileActiveEquitiesService(BaseSyncService):
    """
    Reconcile active equities against provider universe.

    Rules:
    - Missing tickers → mark inactive
    - NEVER reactivate assets
    - NEVER create assets
    """

    name = "equity.universe.reconcile_active"

    @transaction.atomic
    def _sync(self) -> dict:
        provider_symbols = {
            row["symbol"].upper()
            for row in FMP_PROVIDER.get_actively_traded_equities()
            if row.get("symbol")
        }

        identifiers = (
            AssetIdentifier.objects
            .filter(id_type=AssetIdentifier.IdentifierType.TICKER)
            .select_related("asset")
        )

        deactivated = 0
        total = 0

        for ident in identifiers:
            total += 1
            symbol = ident.value.upper()

            if symbol in provider_symbols:
                continue

            asset = ident.asset
            profile, _ = EquityProfile.objects.get_or_create(asset=asset)

            if profile.is_actively_trading:
                profile.is_actively_trading = False
                profile.save(update_fields=["is_actively_trading"])
                deactivated += 1

        logger.info(
            "[EQUITY_RECONCILE] checked=%s deactivated=%s",
            total,
            deactivated,
        )

        return {
            "success": True,
            "checked": total,
            "deactivated": deactivated,
            "provider_count": len(provider_symbols),
        }
