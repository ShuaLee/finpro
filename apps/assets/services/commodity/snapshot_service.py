from django.db import transaction

from assets.models.commodity import CommoditySnapshotID


class CommoditySnapshotService:
    """
    Atomically switches the active commodity snapshot.
    """

    @transaction.atomic
    def swap(self, snapshot_id):
        CommoditySnapshotID.objects.update_or_create(
            id=1,
            defaults={"current_snapshot": snapshot_id},
        )
