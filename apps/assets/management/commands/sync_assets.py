from django.core.management.base import BaseCommand, CommandError

from assets.models.asset_core import Asset, AssetIdentifier, AssetType
from assets.services.syncs.equity import EquitySyncManager


class Command(BaseCommand):
    help = "Sync equity universe or individual equities (identifier/profile/price/dividends)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--universe",
            action="store_true",
            help="Run full equity universe sync from FMP stock-list."
        )

        parser.add_argument(
            "--symbol",
            type=str,
            help="Sync a single equity by ticker (e.g., --symbol AAPL)"
        )

        parser.add_argument(
            "--components",
            nargs="*",
            type=str,
            choices=["identifiers", "profile", "price", "dividends"],
            help="Optional list of components to sync. Default = all."
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform universe sync without DB modifications."
        )

    def handle(self, *args, **options):

        # ============================================================
        # 1. UNIVERSE SYNC
        # ============================================================
        if options["universe"]:
            dry = options["dry_run"]
            self.stdout.write(f"🔄 Running equity universe sync (dry={dry})...")

            results = EquitySyncManager.sync_universe(dry_run=dry)

            self.stdout.write(self.style.SUCCESS("✅ Universe sync complete:"))
            for key, val in results.items():
                self.stdout.write(f" • {key}: {val}")

            return

        # ============================================================
        # 2. INDIVIDUAL EQUITY SYNC
        # ============================================================
        symbol = options.get("symbol")
        if symbol:
            symbol = symbol.upper().strip()

            try:
                equity_type = AssetType.objects.get(slug="equity")
            except AssetType.DoesNotExist:
                raise CommandError(
                    "❌ AssetType slug='equity' not found. Run bootstrap.")

            # Find the asset by ticker
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
                    f"❌ No equity found with ticker '{symbol}'.")

            # Selected components
            components = options.get("components")

            self.stdout.write(
                f"🔄 Syncing equity {symbol} ({asset.name}) "
                f"components={components or 'ALL'}"
            )

            results = EquitySyncManager.sync(asset, components=components)

            self.stdout.write(self.style.SUCCESS("✅ Sync complete:"))
            for k, v in results.items():
                self.stdout.write(f" • {k}: {v}")

            return

        # ============================================================
        # 3. NO VALID ARGUMENTS
        # ============================================================
        raise CommandError(
            "You must pass either --universe or --symbol SYMBOL.\n"
            "Examples:\n"
            "  manage.py sync_equities --universe\n"
            "  manage.py sync_equities --symbol AAPL\n"
            "  manage.py sync_equities --symbol AAPL --components price profile\n"
        )
