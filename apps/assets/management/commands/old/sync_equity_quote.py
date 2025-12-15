from django.core.management.base import BaseCommand, CommandError

from apps.assets.models.asset_core.asset import Asset, AssetIdentifier, AssetType
from assets.services.syncs.equity_sync import EquitySyncService


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

        # -------------------------------------------------------
        # 1. Find system equity type (slug='equity')
        # -------------------------------------------------------
        try:
            equity_type = AssetType.objects.get(slug="equity")
        except AssetType.DoesNotExist:
            raise CommandError(
                "❌ AssetType slug='equity' not found. Did you run bootstrap?"
            )

        # -------------------------------------------------------
        # 2. Lookup asset via TICKER identifier
        # -------------------------------------------------------
        asset = (
            Asset.objects.filter(
                asset_type=equity_type,
                identifiers__id_type=AssetIdentifier.IdentifierType.TICKER,
                identifiers__value=symbol,
            )
            .distinct()
            .first()
        )

        if not asset:
            raise CommandError(
                f"❌ No equity found with ticker '{symbol}'. "
                "Run equity_universe_sync or create it manually."
            )

        self.stdout.write(
            f"🔄 Syncing latest quote for {symbol} ({asset.name})...")

        # -------------------------------------------------------
        # 3. Perform quote sync
        # -------------------------------------------------------
        success = EquitySyncService.sync_quote(asset)

        if success:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Synced quote for {symbol}"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️ Failed to sync quote for {symbol}"
            ))
