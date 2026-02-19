from django.core.management.base import BaseCommand

from assets.services.equity import (
    EquitySeederService,
    EquitySnapshotService,
    EquitySnapshotCleanupService,
    ExchangeSeederService
)


class Command(BaseCommand):
    help = "Rebuild the equity universe using snapshot-based seeding"

    def handle(self, *args, **options):

        self.stdout.write("🏦 Seeding exchanges...")
        ExchangeSeederService().run()

        self.stdout.write("📥 Seeding equities...")
        snapshot_id = EquitySeederService().run()
        self.stdout.write(f"🆕 Snapshot created: {snapshot_id}")

        self.stdout.write("🔁 Activating snapshot...")
        EquitySnapshotService().swap(snapshot_id)

        self.stdout.write("🧹 Cleaning up old snapshots...")
        EquitySnapshotCleanupService().run()

        self.stdout.write(self.style.SUCCESS("✅ Equity DB refresh complete"))
