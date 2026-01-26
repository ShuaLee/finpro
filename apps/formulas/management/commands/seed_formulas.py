from django.core.management.base import BaseCommand
from django.db import transaction

from formulas.seeders.formulas import seed_system_formulas


class Command(BaseCommand):
    help = "Seed system formulas and formula definitions"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🧮 Seeding system formulas...")
        seed_system_formulas()
        self.stdout.write(self.style.SUCCESS("✅ Formula seeding complete"))
