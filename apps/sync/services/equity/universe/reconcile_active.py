# sync/services/equity/universe/reconcile_active.py
import logging

from django.db import transaction

from assets.models.asset_core import AssetIdentifier
from assets.models.profiles.equity_profile import EquityProfile
from external_data.providers.fmp.client import FMP_PROVIDER
from sync.services.base import BaseSyncService

logger = logging.getLogger(__name__)


class ReconcileActiveEquitiesService(BaseSyncService):
    name = "equity.universe.reconcile"

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

        for ident in identifiers:
            if ident.value.upper() in provider_symbols:
                continue

            profile, _ = EquityProfile.objects.get_or_create(
                asset=ident.asset
            )

            if profile.is_actively_trading:
                profile.is_actively_trading = False
                profile.save(update_fields=["is_actively_trading"])
                deactivated += 1

        return {
            "success": True,
            "checked": identifiers.count(),
            "deactivated": deactivated,
        }
