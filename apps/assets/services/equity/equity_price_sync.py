from django.db import transaction

from assets.models.core import AssetPrice
from assets.models.equity import EquityAsset, EquitySnapshotID
from external_data.providers.fmp.client import FMP_PROVIDER
from schemas.services.scv_refresh_service import SCVRefreshService


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
            quote = FMP_PROVIDER.get_equity_quote(equity.ticker)

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

            SCVRefreshService.asset_changed(equity.asset)

            updated += 1

        return {
            "updated": updated,
            "skipped": skipped,
        }
