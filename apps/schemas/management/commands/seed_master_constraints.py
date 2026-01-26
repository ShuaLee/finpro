from django.core.management.base import BaseCommand
from django.db import transaction

from schemas.seeders.master_constraints import seed_master_constraints


class Command(BaseCommand):
    help = "Seed system-level MasterConstraints (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🔧 Seeding master constraints...")
        seed_master_constraints()
        self.stdout.write(self.style.SUCCESS("✅ Master constraints seeded"))
