from django.core.management.base import BaseCommand

from fx.services.country_seeder import CountrySeederService
from fx.services.currency_seeder import FXCurrencySeederService


class Command(BaseCommand):
    help = "Bootstrap FX reference data (countries & currencies)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            help="Deactivate records not present in latest provider data.",
        )

    def handle(self, *args, **options):
        deactivate_missing = options["deactivate_missing"]

        self.stdout.write("Seeding countries...")
        country_summary = CountrySeederService().run(
            deactivate_missing=deactivate_missing,
        )
        self.stdout.write(f"Countries: {country_summary}")

        self.stdout.write("Seeding currencies...")
        currency_summary = FXCurrencySeederService().run(
            deactivate_missing=deactivate_missing,
        )
        self.stdout.write(f"Currencies: {currency_summary}")

        self.stdout.write(self.style.SUCCESS("FX bootstrap complete"))
