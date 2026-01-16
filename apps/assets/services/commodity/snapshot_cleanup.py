from django.db import transaction

from assets.models.core import Asset
from assets.models.commodity import CommodityAsset, CommoditySnapshotID


class CommoditySnapshotCleanupService:
    """
    Deletes all commodity assets NOT in the active snapshot,
    including their underlying Asset rows.
    """

    @transaction.atomic
    def run(self):
        snapshot_row = CommoditySnapshotID.objects.first()
        if not snapshot_row:
            return

        asset_ids = CommodityAsset.objects.exclude(
            snapshot_id=snapshot_row.current_snapshot
        ).values_list("asset_id", flat=True)

        Asset.objects.filter(id__in=asset_ids).delete()
