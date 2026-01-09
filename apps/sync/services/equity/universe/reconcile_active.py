import logging

from django.db import transaction

from assets.models.asset_core import AssetIdentifier
from assets.models.profiles.equity_profile import EquityProfile
from external_data.providers.fmp.client import FMP_PROVIDER
from sync.services.base import BaseSyncService

logger = logging.getLogger(__name__)


class ReconcileActiveEquitiesService(BaseSyncService):
    """
    Reconcile active equities against provider universe.

    Rules:
    - If a ticker exists in DB but NOT in provider list → deactivate
    - NEVER reactivate assets
    - NEVER create assets
    - Identity conflicts are NOT handled here
    """

    name = "equity.universe.reconcile_active"

    @transaction.atomic
    def _sync(self) -> dict:
        # ----------------------------------
        # Fetch provider universe
        # ----------------------------------
        provider_symbols = {
            row["symbol"].upper()
            for row in FMP_PROVIDER.get_actively_traded_equities()
            if row.get("symbol")
        }

        # ----------------------------------
        # Iterate all equity tickers
        # ----------------------------------
        ticker_idents = (
            AssetIdentifier.objects
            .filter(id_type=AssetIdentifier.IdentifierType.TICKER)
            .select_related("asset")
        )

        checked = 0
        deactivated = 0

        for ident in ticker_idents:
            checked += 1
            symbol = ident.value.upper()

            if symbol in provider_symbols:
                continue

            profile, _ = EquityProfile.objects.get_or_create(
                asset=ident.asset
            )

            if profile.is_actively_trading:
                profile.is_actively_trading = False
                profile.save(update_fields=["is_actively_trading"])
                deactivated += 1

        logger.info(
            "[RECONCILE_ACTIVE] checked=%s deactivated=%s provider_count=%s",
            checked,
            deactivated,
            len(provider_symbols),
        )

        return {
            "success": True,
            "checked": checked,
            "deactivated": deactivated,
            "provider_count": len(provider_symbols),
        }
