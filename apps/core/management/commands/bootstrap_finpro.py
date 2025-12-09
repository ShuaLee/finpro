from django.core.management.base import BaseCommand
from django.db import transaction

# --- FX + Countries ---
from fx.services.sync import FXSyncService
from fx.services.country_sync import CountrySyncService

# --- Exchanges ---
from assets.services.seeds.seed_exchanges import seed_exchanges

# --- Datatypes + Constraints ---
from datatype.services.seeds.seed_datatypes import seed_datatypes
from datatype.services.seeds.seed_constraint_types import seed_constraint_types
from datatype.services.seeds.seed_constraint_definitions import seed_constraint_definitions

# --- Asset Types ---
from assets.services.seeds.seed_asset_types import seed_asset_types

# --- NEW: Sectors + Industries ---
from assets.services.seeds.classifications import ClassificationSeeder


class Command(BaseCommand):
    help = (
        "Bootstrap FX currencies, Countries, Exchanges, AssetTypes, "
        "Sectors, Industries, DataTypes, ConstraintTypes, and ConstraintDefinitions."
    )

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(self.style.WARNING(
            "\n🚀 Starting Core System + Datatype + Classifications bootstrap...\n"
        ))

        # ============================================================
        # 0. Sync Countries
        # ============================================================
        self.stdout.write("🌍 Syncing countries...")
        country_count = CountrySyncService.sync_countries()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ Countries synced ({country_count} updated)\n"))

        # ============================================================
        # 1. Sync FX Currencies
        # ============================================================
        self.stdout.write("💱 Syncing FX currencies...")
        fx_count = FXSyncService.sync_currencies()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ FX currencies synced ({fx_count} new)\n"))

        # ============================================================
        # 2. Seed Exchanges (requires Countries)
        # ============================================================
        self.stdout.write("🏛  Seeding Exchanges...")
        exchange_count = seed_exchanges()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ Exchanges seeded: {exchange_count}\n"))

        # ============================================================
        # 3. Seed AssetTypes
        # ============================================================
        self.stdout.write("🧩 Seeding AssetTypes...")
        asset_count = seed_asset_types()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ AssetTypes seeded ({asset_count})\n"))

        # ============================================================
        # 4. Seed Sectors + Industries
        # ============================================================
        self.stdout.write("🏷  Seeding Sectors & Industries from FMP...")
        classifications = ClassificationSeeder.seed_all()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ Sectors created: {classifications['sectors']['created']}, "
            f"updated: {classifications['sectors']['updated']}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ Industries created: {classifications['industries']['created']}, "
            f"updated: {classifications['industries']['updated']}\n"
        ))

        # ============================================================
        # 5. Seed DataTypes
        # ============================================================
        self.stdout.write("🔡 Seeding DataTypes...")
        dt_count = seed_datatypes()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ DataTypes seeded ({dt_count} created)\n"))

        # ============================================================
        # 6. Seed Constraint Types
        # ============================================================
        self.stdout.write("🧩 Seeding Constraint Types...")
        ct_count = seed_constraint_types()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ Constraint Types seeded ({ct_count} created)\n"))

        # ============================================================
        # 7. Seed Constraint Definitions
        # ============================================================
        self.stdout.write("📏 Seeding Constraint Definitions...")
        cd_count = seed_constraint_definitions()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ Constraint Definitions seeded ({cd_count} created)\n"))

        # ============================================================
        # DONE
        # ============================================================
        self.stdout.write(self.style.SUCCESS(
            "🎉 Core bootstrap complete!\n"
        ))
