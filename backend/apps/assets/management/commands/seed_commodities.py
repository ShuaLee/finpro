from django.core.management.base import BaseCommand
from django.db import transaction

from assets.models.commodity.precious_metal import PreciousMetalAsset
from assets.services.commodity import (
    CommoditySeederService,
    CommoditySnapshotService,
    CommoditySnapshotCleanupService,
)
from assets.services.commodity.constants import PRECIOUS_METAL_COMMODITY_MAP
from assets.models.core import Asset, AssetType
from assets.models.commodity import CommodityAsset, CommoditySnapshotID


class Command(BaseCommand):
    help = "Rebuild the commodity universe using snapshot-based seeding"

    @transaction.atomic
    def handle(self, *args, **options):

        # 1️⃣ Seed commodities
        self.stdout.write("📥 Seeding commodities...")
        snapshot_id = CommoditySeederService().run()
        self.stdout.write(f"🆕 Snapshot created: {snapshot_id}")

        # 2️⃣ Activate snapshot
        self.stdout.write("🔁 Activating snapshot...")
        CommoditySnapshotService().swap(snapshot_id)

        # 3️⃣ Sync precious metals FIRST
        self.stdout.write("🪙 Syncing precious metals...")
        self._sync_precious_metals()

        # 4️⃣ NOW cleanup stale commodities
        self.stdout.write("🧹 Cleaning up old snapshots...")
        CommoditySnapshotCleanupService().run()

        self.stdout.write(
            self.style.SUCCESS("✅ Commodity DB refresh complete")
        )


    def _sync_precious_metals(self):
        pm_asset_type = AssetType.objects.get(slug="precious_metal")

        snapshot = CommoditySnapshotID.objects.first()
        if not snapshot:
            return

        active_commodities = {
            c.symbol: c
            for c in CommodityAsset.objects.filter(
                snapshot_id=snapshot.current_snapshot
            )
        }

        for metal, commodity_symbol in PRECIOUS_METAL_COMMODITY_MAP.items():
            commodity = active_commodities.get(commodity_symbol)
            if not commodity:
                continue

            pm = (
                PreciousMetalAsset.objects
                .select_related("asset")
                .filter(metal=metal)
                .first()
            )

            if pm:
                # Only update commodity reference
                if pm.commodity_id != commodity.asset_id:
                    pm.commodity = commodity
                    pm.save(update_fields=["commodity"])
            else:
                # Create once, then never recreate again
                asset = Asset.objects.create(
                    asset_type=pm_asset_type,
                )

                PreciousMetalAsset.objects.create(
                    asset=asset,
                    metal=metal,
                    commodity=commodity,
                )
