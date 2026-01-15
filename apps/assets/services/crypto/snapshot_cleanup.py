from django.db import transaction

from assets.models.core import Asset
from assets.models.crypto import CryptoAsset, CryptoSnapshotID


class CryptoSnapshotCleanupService:
    """
    Deletes all crypto assets NOT in the active snapshot,
    including their underlying Asset rows.
    """

    @transaction.atomic
    def run(self):
        snapshot_row = CryptoSnapshotID.objects.first()
        if not snapshot_row:
            return

        # Find underlying Asset IDs for stale crypto assets
        asset_ids = CryptoAsset.objects.exclude(
            snapshot_id=snapshot_row.current_snapshot
        ).values_list("asset_id", flat=True)

        # Delete Assets (cascades to CryptoAsset)
        Asset.objects.filter(id__in=asset_ids).delete()
