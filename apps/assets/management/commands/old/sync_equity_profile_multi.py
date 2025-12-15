from django.core.management.base import BaseCommand, CommandError

from apps.assets.models.asset_core.asset import Asset, AssetIdentifier, AssetType
from assets.services.syncs.equity_sync import EquitySyncService


class Command(BaseCommand):
    help = "Sync the profile (multi-result) for a single equity by ticker symbol."

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="Ticker symbol of the equity (e.g., AAPL, MSFT)",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"].upper().strip()

        # -------------------------------------------------------
        # 1. Resolve system equity type
        # -------------------------------------------------------
        try:
            equity_type = AssetType.objects.get(slug="equity")
        except AssetType.DoesNotExist:
            raise CommandError(
                "❌ System AssetType with slug='equity' not found. "
                "Ensure asset types are seeded first."
            )

        # -------------------------------------------------------
        # 2. Find the asset by its TICKER identifier
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
                "Make sure the equity is created or imported first."
            )

        self.stdout.write(
            f"🔄 Multi-profile sync for {symbol} ({asset.name})...")

        # -------------------------------------------------------
        # 3. Run the new multi-profile sync
        # -------------------------------------------------------
        success = EquitySyncService.sync_profile_multi(asset)

        if success:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Synced profile for {symbol} using multi-result fetch"))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️ Failed to sync profile for {symbol} using multi-result fetch"))
