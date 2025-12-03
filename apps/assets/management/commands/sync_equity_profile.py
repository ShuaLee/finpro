
from django.core.management.base import BaseCommand, CommandError
from assets.models.assets import Asset, AssetIdentifier
from assets.services.syncs.equity_sync import EquitySyncService
from core.types import DomainType


class Command(BaseCommand):
    help = "Sync the profile for a single equity (by ticker symbol)."

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="Ticker symbol of the equity (e.g., AAPL, MSFT)",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"].upper().strip()

        # Find the asset by its primary ticker
        asset = (
            Asset.objects.filter(
                identifiers__value=symbol,
                identifiers__id_type=AssetIdentifier.IdentifierType.TICKER,
                asset_type__domain=DomainType.EQUITY,
            )
            .distinct()
            .first()
        )

        if not asset:
            raise CommandError(
                f"❌ No equity found with ticker '{symbol}'. "
                "Seed the universe first or create it manually."
            )

        self.stdout.write(f"🔄 Syncing profile for {symbol} ({asset.name})...")

        success = EquitySyncService.sync_profile(asset)

        if success:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Synced profile for {symbol}"))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️ Failed to sync profile for {symbol}"))
