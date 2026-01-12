from django.db import transaction

from assets.models.equity import EquityAsset
from assets.models.core import AssetPrice
from assets.models.equity import EquitySnapshotID
from external_data.providers.fmp.client import FMP_PROVIDER


class EquityPriceSyncService:
    """
    Updates prices for the ACTIVE equity snapshot only.
    """

    @transaction.atomic
    def run(self):
        snapshot = EquitySnapshotID.obejcts.get(id=1).current_snapshot

        equities = EquityAsset.objects.filter(
            snapshot_id=snapshot
        ).select_related("asset")

        for equity in equities:
            quote = FMP_PROVIDER.get_equity_quote(equity.ticker)
            if not quote or quote.price is None:
                continue

            AssetPrice.objects.update_or_create(
                asset=equity.asset,
                defaults={
                    "price": quote.price,
                    "source": "FMP",
                },
            )
