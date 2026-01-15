from django.db import transaction
from assets.models.crypto import CryptoSnapshotID


class CryptoSnapshotService:
    """
    Atomically switches the active crypto snapshot.
    """

    @transaction.atomic
    def swap(self, snapshot_id):
        CryptoSnapshotID.objects.update_or_create(
            id=1,
            defaults={"current_snapshot": snapshot_id},
        )
