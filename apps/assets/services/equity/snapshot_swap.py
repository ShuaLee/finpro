from django.db import transaction
from assets.models.equity import EquityAsset
from assets.models.equity import EquitySnapshot


class EquitySnapshotService:
    """
    Atomically switches the active equity snapshot.
    """

    @transaction.atomic
    def swap(self, snapshot_id):
        EquitySnapshot.update_or_create(
            id=1,
            defaults={"current_snapshot": snapshot_id},
        )
