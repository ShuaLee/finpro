from django.core.management.base import BaseCommand
from django.db import transaction

from schemas.seeders.system_column_categories import seed_system_column_categories


class Command(BaseCommand):
    help = "Seed system schema column categories."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding schema column categories...")
        seed_system_column_categories()
        self.stdout.write(self.style.SUCCESS("Schema column categories seeded."))
