from django.db import transaction

from assets.models.core import Asset
from assets.models.equity import EquityAsset, EquitySnapshotID


class EquitySnapshotCleanupService:
    """
    Deletes all equity assets NOT in the active snapshot,
    including their underlying Asset rows.
    """

    @transaction.atomic
    def run(self):
        snapshot_row = EquitySnapshotID.objects.first()
        if not snapshot_row:
            return  # nothing to clean yet

        # Find underlying Asset IDs for stale equity assets
        asset_ids = EquityAsset.objects.exclude(
            snapshot_id=snapshot_row.current_snapshot
        ).values_list("asset_id", flat=True)

        # Delete Assets (cascades to EquityAsset)
        Asset.objects.filter(id__in=asset_ids).delete()
