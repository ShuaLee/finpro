from django.core.management.base import BaseCommand, CommandError
from assets.models.assets import Asset, AssetIdentifier
from assets.services.syncs.equity_sync import EquitySyncService
from core.types import DomainType


class Command(BaseCommand):
    help = "Sync the latest quote for a single equity (by ticker symbol)."

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="Ticker symbol of the equity (e.g., AAPL, MSFT, SPY)",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"].upper().strip()

        # ✅ Correct way: find asset via TICKER identifier
        asset = (
            Asset.objects.filter(
                identifiers__value=symbol,
                identifiers__id_type=AssetIdentifier.IdentifierType.TICKER,
                asset_type=DomainType.EQUITY,
            )
            .distinct()
            .first()
        )

        if not asset:
            raise CommandError(
                f"❌ No equity found in DB with ticker '{symbol}'. "
                "Seed the universe first or create it manually."
            )

        self.stdout.write(f"🔄 Syncing quote for {symbol} ({asset.name})...")

        success = EquitySyncService.sync_quote(asset)

        if success:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Synced quote for {symbol}"))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️ Failed to sync quote for {symbol}"))
