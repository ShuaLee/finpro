from django.core.management.base import BaseCommand, CommandError
from assets.models.assets import Asset, AssetIdentifier
from assets.services.syncs.crypto_sync import CryptoSyncService
from core.types import DomainType


class Command(BaseCommand):
    help = "Sync the latest quote for a single cryptocurrency (by pair symbol, e.g., BTCUSD)."

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="Crypto pair symbol (e.g., BTCUSD, ETHUSD).",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"].upper().strip()

        # 🔎 Find crypto via primary PAIR_SYMBOL identifier
        asset = (
            Asset.objects.filter(
                asset_type__domain=DomainType.CRYPTO,
                identifiers__id_type=AssetIdentifier.IdentifierType.PAIR_SYMBOL,
                identifiers__value=symbol,
            )
            .distinct()
            .first()
        )

        if not asset:
            raise CommandError(
                f"❌ No crypto asset found with pair '{symbol}'. "
                "Run crypto_sync_universe first or create manually."
            )

        self.stdout.write(f"🔄 Syncing quote for {symbol} ({asset.name})...")

        success = CryptoSyncService.sync_quote(asset)

        if success:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Synced crypto quote for {symbol}"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️ Failed to sync quote for {symbol}"
            ))
