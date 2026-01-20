from django.core.management.base import BaseCommand, CommandError

from fx.services.fx_rate_fetcher import FXRateFetcherService
from external_data.exceptions import ExternalDataEmptyResult


class Command(BaseCommand):
    help = "Fetch and persist a live FX rate (e.g. EURUSD)"

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="FX symbol (e.g. EURUSD)",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"]

        self.stdout.write(f"💱 Fetching FX rate for {symbol}...")

        try:
            fx_rate = FXRateFetcherService().run(symbol)
        except ExternalDataEmptyResult as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Failed to fetch FX rate: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ {fx_rate.from_currency.code} → {fx_rate.to_currency.code} = {fx_rate.rate}"
            )
        )
