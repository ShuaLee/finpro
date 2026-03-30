from django.core.management.base import BaseCommand, CommandError

from assets.services.crypto.crypto_price_sync import CryptoPriceSyncService


class Command(BaseCommand):
    help = "Sync the latest price for a single crypto pair (active snapshot only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="Crypto pair symbol (e.g. BTCUSD, ETHUSD)",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"].upper().strip()

        self.stdout.write(f"💰 Syncing price for {symbol}...")

        service = CryptoPriceSyncService()
        result = service.run(symbol=symbol)

        if result["updated"] == 0:
            raise CommandError(f"No price updated for {symbol}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Price synced for {symbol}"
            )
        )
