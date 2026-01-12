from assets.models.equity import EquityAsset, EquitySnapshotID


class EquitySnapshotCleanupService:
    """
    Deletes all equity assets NOT in the active snapshot.
    """

    def run(self):
        snapshot_row = EquitySnapshotID.objects.first()
        if not snapshot_row:
            return  # nothing to clean yet

        EquityAsset.objects.exclude(
            snapshot_id=snapshot_row.current_snapshot
        ).delete()
