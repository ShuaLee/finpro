from django.core.management.base import BaseCommand

from assets.services.commodity import (
    CommoditySeederService,
    CommoditySnapshotService,
    CommoditySnapshotCleanupService,
)


class Command(BaseCommand):
    help = "Rebuild the commodity universe using snapshot-based seeding"

    def handle(self, *args, **options):
        self.stdout.write("📥 Seeding commodities...")
        snapshot_id = CommoditySeederService().run()
        self.stdout.write(f"🆕 Snapshot created: {snapshot_id}")

        self.stdout.write("🔁 Activating snapshot...")
        CommoditySnapshotService().swap(snapshot_id)

        self.stdout.write("🧹 Cleaning up old snapshots...")
        CommoditySnapshotCleanupService().run()

        self.stdout.write(
            self.style.SUCCESS("✅ Commodity DB refresh complete")
        )
