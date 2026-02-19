from django.db import transaction
from assets.models.equity import EquitySnapshotID


class EquitySnapshotService:
    """
    Atomically switches the active equity snapshot.
    """

    @transaction.atomic
    def swap(self, snapshot_id):
        EquitySnapshotID.objects.update_or_create(
            id=1,
            defaults={"current_snapshot": snapshot_id},
        )
