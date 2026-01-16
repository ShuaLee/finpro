from django.core.management.base import BaseCommand, CommandError

from assets.services.commodity.commodity_price_sync import (
    CommodityPriceSyncService,
)


class Command(BaseCommand):
    help = "Sync the latest price for a single commodity (active snapshot only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="Commodity symbol (e.g. GCUSD, CLUSD)",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"].upper().strip()

        self.stdout.write(f"💰 Syncing price for {symbol}...")

        service = CommodityPriceSyncService()
        result = service.run(symbol=symbol)

        if result["updated"] == 0:
            raise CommandError(f"No price updated for {symbol}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Price synced for {symbol}"
            )
        )
