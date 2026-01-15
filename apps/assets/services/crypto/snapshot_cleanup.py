from assets.models.crypto import CryptoAsset, CryptoSnapshotID


class CryptoSnapshotCleanupService:
    """
    Deletes all crypto assets NOT in the active snapshot.
    """

    def run(self):
        snapshot_row = CryptoSnapshotID.objects.first()
        if not snapshot_row:
            return

        CryptoAsset.objects.exclude(
            snapshot_id=snapshot_row.current_snapshot
        ).delete()
