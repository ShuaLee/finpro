from django.db import transaction

from assets.models.core import AssetPrice
from assets.models.crypto import CryptoAsset, CryptoSnapshotID
from external_data.providers.fmp.client import FMP_PROVIDER
from schemas.services.scv_refresh_service import SCVRefreshService

class CryptoPriceSyncService:
    """
    Updates prices for crypto assets in the ACTIVE snapshot.
    Can optionally sync a single crypto pair.
    """

    @transaction.atomic
    def run(self, *, symbol: str | None = None) -> dict:
        snapshot_row = CryptoSnapshotID.objects.first()
        if not snapshot_row:
            return {"updated": 0, "skipped": 0}

        snapshot = snapshot_row.current_snapshot

        qs = CryptoAsset.objects.filter(snapshot_id=snapshot)

        if symbol:
            qs = qs.filter(pair_symbol__iexact=symbol)

        updated = 0
        skipped = 0

        for crypto in qs.select_related("asset"):
            try:
                quote = FMP_PROVIDER.get_crypto_quote(crypto.pair_symbol)
            except Exception:
                skipped += 1
                continue

            price = quote.get("price")
            if price is None:
                skipped += 1
                continue

            AssetPrice.objects.update_or_create(
                asset=crypto.asset,
                defaults={
                    "price": price,
                    "source": FMP_PROVIDER.name,
                },
            )

            SCVRefreshService.asset_changed(crypto.asset)

            updated += 1

        return {
            "updated": updated,
            "skipped": skipped,
        }
