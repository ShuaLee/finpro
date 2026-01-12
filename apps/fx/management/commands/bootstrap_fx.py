from django.core.management.base import BaseCommand

from fx.services.country_seeder import CountrySeederService
from fx.services.currency_seeder import FXCurrencySeederService


class Command(BaseCommand):
    help = "Bootstrap FX reference data (countries & currencies)"

    def handle(self, *args, **options):
        self.stdout.write("🌍 Seeding countries...")
        CountrySeederService().run()

        self.stdout.write("💱 Seeding currencies...")
        FXCurrencySeederService().run()

        self.stdout.write(self.style.SUCCESS("✅ FX bootstrap complete"))
