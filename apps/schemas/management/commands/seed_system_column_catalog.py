from django.core.management.base import BaseCommand
from django.db import transaction

from schemas.seeders.system_columns import seed_system_column_catalog


class Command(BaseCommand):
    help = "Seed system-wide schema column templates and behaviors."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding system column catalog...")
        seed_system_column_catalog()
        self.stdout.write(self.style.SUCCESS("System column catalog seeded."))
