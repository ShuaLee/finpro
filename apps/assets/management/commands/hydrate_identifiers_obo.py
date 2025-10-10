import logging
from django.core.management.base import BaseCommand
from assets.models.assets import Asset, AssetIdentifier
from assets.services.syncs.equity_sync import EquitySyncService
from core.types import DomainType
from external_data.fmp.equities.fetchers import fetch_equity_profile_raw

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Hydrate missing ISIN / CUSIP / CIK identifiers for a specific equity in the DB."

    def add_arguments(self, parser):
        parser.add_argument(
            "symbol",
            type=str,
            help="Ticker symbol of the equity (e.g., FRO, AAPL, MSFT)",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"].upper().strip()
        self.stdout.write(
            f"🔍 Attempting to hydrate identifiers for {symbol}...")

        # --- Ensure the asset exists ---
        asset = (
            Asset.objects.filter(
                asset_type=DomainType.EQUITY,
                identifiers__value=symbol,
                identifiers__id_type=AssetIdentifier.IdentifierType.TICKER,
            )
            .distinct()
            .first()
        )

        if not asset:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ No equity found in DB for symbol '{symbol}'. Seed first!")
            )
            return

        # --- Bail out if identifiers already exist ---
        existing_ids = asset.identifiers.filter(
            id_type__in=[
                AssetIdentifier.IdentifierType.ISIN,
                AssetIdentifier.IdentifierType.CUSIP,
                AssetIdentifier.IdentifierType.CIK,
            ]
        )

        if existing_ids.exists():
            self.stdout.write(self.style.SUCCESS(
                f"✅ {symbol} already has identifiers:"))
            for ident in existing_ids:
                self.stdout.write(f"   • {ident.id_type}: {ident.value}")
            return

        # --- Fetch raw profile from FMP ---
        self.stdout.write(f"🌐 Fetching profile for {symbol} from FMP...")
        profile = None
        try:
            ticker = EquitySyncService._get_primary_ticker(asset)
            if not ticker:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️ No primary ticker found, cannot fetch profile.")
                )
                return

            profile = fetch_equity_profile_raw(ticker)
            if not profile:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ No profile data found for {symbol}.")
                )
                return

        except Exception as e:
            logger.error(
                f"Failed to fetch raw profile for {symbol}: {e}", exc_info=True)
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Failed to fetch profile for {symbol}: {e}")
            )
            return

        # --- Hydrate identifiers ---
        self.stdout.write("🧩 Hydrating identifiers...")
        EquitySyncService.hydrate_identifiers(asset, profile)

        # --- Confirm ---
        hydrated = asset.identifiers.filter(
            id_type__in=[
                AssetIdentifier.IdentifierType.ISIN,
                AssetIdentifier.IdentifierType.CUSIP,
                AssetIdentifier.IdentifierType.CIK,
            ]
        )
        if hydrated.exists():
            self.stdout.write(self.style.SUCCESS(
                f"✅ Hydrated identifiers for {symbol}:"))
            for ident in hydrated:
                self.stdout.write(f"   • {ident.id_type}: {ident.value}")
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ No identifiers found in profile response for {symbol}.")
            )
