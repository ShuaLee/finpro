from assets.models.equity import EquityAsset
from assets.models.equity import EquitySnapshot


class EquitySnapshotCleanupService:
    def run(self):
        current = EquitySnapshot.objects.get(id=1).current_snapshot

        EquityAsset.objects.exclude(
            snapshot_id=current
        ).delete()
