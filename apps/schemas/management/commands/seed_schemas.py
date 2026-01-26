from django.core.management.base import BaseCommand
from django.db import transaction

from schemas.seeders.constraints import seed_master_constraints
from schemas.seeders.base import seed_base_schema
from schemas.seeders.brokerage import seed_brokerage_schema


class Command(BaseCommand):
    help = "Seed system schema infrastructure"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🔧 Seeding constraints...")
        seed_master_constraints()

        self.stdout.write("📐 Seeding base schema...")
        seed_base_schema()

        self.stdout.write("🏦 Seeding brokerage schema...")
        seed_brokerage_schema()

        self.stdout.write(self.style.SUCCESS("✅ Schema seeding complete"))
