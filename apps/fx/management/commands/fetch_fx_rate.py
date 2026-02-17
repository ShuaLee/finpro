from django.core.management.base import BaseCommand, CommandError

from external_data.exceptions import ExternalDataEmptyResult
from fx.services.fx_rate_fetcher import FXRateFetcherService


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

        self.stdout.write(f"Fetching FX rate for {symbol}...")

        try:
            fx_rate = FXRateFetcherService().run(symbol)
        except ExternalDataEmptyResult as exc:
            raise CommandError(str(exc))
        except Exception as exc:
            raise CommandError(f"Failed to fetch FX rate: {exc}")

        self.stdout.write(
            self.style.SUCCESS(
                f"{fx_rate.from_currency.code} -> {fx_rate.to_currency.code} = {fx_rate.rate}"
            )
        )
