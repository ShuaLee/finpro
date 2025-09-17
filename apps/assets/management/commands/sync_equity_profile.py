from django.core.management.base import BaseCommand, CommandError
from assets.models.asset import Asset
from assets.services.syncs.equity_sync import EquitySyncService
from core.types import DomainType


class Command(BaseCommand):
    help = "Sync the profile for a single equity (by symbol)."

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="Ticker symbol of the equity (e.g., AAPL, MSFT)",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"].upper()

        try:
            asset = Asset.objects.get(symbol=symbol, asset_type=DomainType.EQUITY)
        except Asset.DoesNotExist:
            raise CommandError(f"Equity with symbol {symbol} not found in DB. Seed first!")

        success = EquitySyncService.sync_profile(asset)

        if success:
            self.stdout.write(self.style.SUCCESS(f"✅ Synced profile for {symbol}"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ Failed to sync profile for {symbol}"))
