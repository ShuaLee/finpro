from django.db import transaction

from assets.models.core import AssetPrice
from assets.models.equity import EquityAsset, EquitySnapshotID
from external_data.exceptions import ExternalDataError
from external_data.providers.fmp.client import FMP_PROVIDER


def _notify_asset_changed(asset):
    try:
        from schemas.services.orchestration import SchemaOrchestrationService
    except Exception:
        return
    SchemaOrchestrationService.asset_changed(asset)


class EquityPriceSyncService:
    """
    Updates prices for equities in the ACTIVE snapshot.
    Can optionally sync a single ticker.
    """

    @transaction.atomic
    def run(self, *, ticker: str | None = None) -> dict:
        snapshot = EquitySnapshotID.objects.get(id=1).current_snapshot

        qs = EquityAsset.objects.filter(snapshot_id=snapshot)

        if ticker:
            qs = qs.filter(ticker__iexact=ticker)

        updated = 0
        skipped = 0

        for equity in qs.select_related("asset"):
            try:
                quote = FMP_PROVIDER.get_equity_quote(equity.ticker)
            except ExternalDataError:
                skipped += 1
                continue

            if not quote or quote.price is None:
                skipped += 1
                continue

            AssetPrice.objects.update_or_create(
                asset=equity.asset,
                defaults={
                    "price": quote.price,
                    "source": FMP_PROVIDER.name,
                },
            )

            _notify_asset_changed(equity.asset)

            updated += 1

        return {
            "updated": updated,
            "skipped": skipped,
        }
