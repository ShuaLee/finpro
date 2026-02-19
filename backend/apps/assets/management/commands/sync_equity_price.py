from django.core.management.base import BaseCommand, CommandError

from assets.services.equity.equity_price_sync import EquityPriceSyncService


class Command(BaseCommand):
    help = "Sync the latest price for a single equity ticker (active snapshot only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "ticker",
            type=str,
            help="Equity ticker symbol (e.g. AAPL, MSFT)",
        )

    def handle(self, *args, **options):
        ticker = options["ticker"].upper().strip()

        self.stdout.write(f"💰 Syncing price for {ticker}...")

        service = EquityPriceSyncService()
        result = service.run(ticker=ticker)

        if result["updated"] == 0:
            raise CommandError(f"No price updated for {ticker}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Price synced for {ticker}"
            )
        )
