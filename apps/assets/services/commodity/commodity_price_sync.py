from django.db import transaction

from assets.models.core import AssetPrice
from assets.models.commodity import CommodityAsset, CommoditySnapshotID
from external_data.providers.fmp.client import FMP_PROVIDER
from schemas.services.orchestration import SchemaOrchestrationService


class CommodityPriceSyncService:
    """
    Updates prices for commodity assets in the ACTIVE snapshot.
    Can optionally sync a single commodity symbol.
    """

    @transaction.atomic
    def run(self, *, symbol: str | None = None) -> dict:
        snapshot_row = CommoditySnapshotID.objects.first()
        if not snapshot_row:
            return {"updated": 0, "skipped": 0}

        snapshot = snapshot_row.current_snapshot

        qs = CommodityAsset.objects.filter(snapshot_id=snapshot)

        if symbol:
            qs = qs.filter(symbol__iexact=symbol)

        updated = 0
        skipped = 0

        for commodity in qs.select_related("asset"):
            try:
                quote = FMP_PROVIDER.get_commodity_quote(commodity.symbol)
            except Exception:
                skipped += 1
                continue

            price = quote.price
            if price is None:
                skipped += 1
                continue

            AssetPrice.objects.update_or_create(
                asset=commodity.asset,
                defaults={
                    "price": price,
                    "source": FMP_PROVIDER.name,
                },
            )

            SchemaOrchestrationService.asset_changed(commodity.asset)

            updated += 1

        return {
            "updated": updated,
            "skipped": skipped,
        }
