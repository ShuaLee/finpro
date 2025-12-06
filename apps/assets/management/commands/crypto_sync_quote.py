from django.core.management.base import BaseCommand, CommandError

from assets.models.assets import Asset, AssetIdentifier, AssetType
from assets.services.syncs.crypto_sync import CryptoSyncService


class Command(BaseCommand):
    help = "Sync the latest quote for a single cryptocurrency (by pair symbol, e.g., BTCUSD)."

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="Crypto pair identifier (e.g., BTCUSD, ETHUSD).",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"].upper().strip()

        # --------------------------------------------------------
        # 1. Resolve AssetType for crypto (slug = 'crypto')
        # --------------------------------------------------------
        try:
            crypto_type = AssetType.objects.get(slug="crypto")
        except AssetType.DoesNotExist:
            raise CommandError(
                "❌ System crypto AssetType (slug='crypto') not found.")

        # --------------------------------------------------------
        # 2. Find Asset by PAIR_SYMBOL identifier
        # --------------------------------------------------------
        asset = (
            Asset.objects.filter(
                asset_type=crypto_type,
                identifiers__id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
                identifiers__value=symbol,
            )
            .distinct()
            .first()
        )

        if not asset:
            raise CommandError(
                f"❌ No crypto asset found with pair '{symbol}'.\n"
                "Run crypto_sync_universe first or create the asset manually."
            )

        self.stdout.write(
            f"🔄 Syncing crypto quote for {symbol} ({asset.name})...")

        # --------------------------------------------------------
        # 3. Perform sync
        # --------------------------------------------------------
        success = CryptoSyncService.sync_quote(asset)

        if success:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Synced crypto quote for {symbol}"))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️ Failed to sync quote for {symbol}"))
