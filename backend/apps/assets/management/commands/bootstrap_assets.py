from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bootstrap assets system data (types + optional market universes)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-market-data",
            action="store_true",
            help="Skip market universe refresh (equities/crypto/commodities).",
        )

    def handle(self, *args, **options):
        skip_market_data = options["skip_market_data"]

        self.stdout.write("Seeding system asset types...")
        call_command("seed_asset_types")

        self.stdout.write("Seeding real-estate reference types...")
        call_command("seed_real_estate_types")

        if skip_market_data:
            self.stdout.write(self.style.WARNING("Skipping market data seeding."))
        else:
            self.stdout.write("Refreshing crypto universe...")
            call_command("seed_cryptos")

            self.stdout.write("Refreshing equity universe...")
            call_command("seed_equities")

            self.stdout.write("Refreshing commodity universe...")
            call_command("seed_commodities")

        self.stdout.write(self.style.SUCCESS("Assets bootstrap complete."))
