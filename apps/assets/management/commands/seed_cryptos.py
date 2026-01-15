from django.core.management.base import BaseCommand

from assets.services.core import AssetTypeSeeder
from assets.services.crypto import (
    CryptoSeederService,
    CryptoSnapshotService,
    CryptoSnapshotCleanupService,
)


class Command(BaseCommand):
    help = "Rebuild the crypto universe using snapshot-based seeding"

    def handle(self, *args, **options):
        self.stdout.write("🧱 Ensuring AssetTypes...")
        AssetTypeSeeder.run()

        self.stdout.write("📥 Seeding cryptocurrencies...")
        snapshot_id = CryptoSeederService().run()
        self.stdout.write(f"🆕 Snapshot created: {snapshot_id}")

        self.stdout.write("🔁 Activating snapshot...")
        CryptoSnapshotService().swap(snapshot_id)

        self.stdout.write("🧹 Cleaning up old snapshots...")
        CryptoSnapshotCleanupService().run()

        self.stdout.write(
            self.style.SUCCESS("✅ Crypto DB refresh complete")
        )
