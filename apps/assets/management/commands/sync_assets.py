from django.core.management.base import BaseCommand, CommandError

from assets.models.asset_core import Asset, AssetIdentifier, AssetType
from assets.services.syncs.managers import AssetSyncManager


class Command(BaseCommand):
    help = (
        "Universal asset sync command. Supports:\n"
        " - full universe sync (per asset type)\n"
        " - deep sync for all assets\n"
        " - targeted sync for a single asset\n"
        " - selective sync (profile, quote, dividends, identifiers)"
    )

    def add_arguments(self, parser):
        # -------------------------------
        # Required: asset type
        # -------------------------------
        parser.add_argument(
            "--type",
            type=str,
            required=True,
            help="Asset type slug (equity, crypto, real_state, custom)."
        )

        # -------------------------------
        # Optional: target a single symbol
        # -------------------------------
        parser.add_argument(
            "--symbol",
            type=str,
            help="Sync a single asset by its primary identifier (e.g., AAPL)."
        )

        # -------------------------------
        # Universe Sync
        # -------------------------------
        parser.add_argument(
            "--include-universe",
            action="store_true",
            help="Run a universe sync before deep sync.",
        )
        parser.add_argument(
            "--exchange",
            type=str,
            help="Optional exchange filter for equities (e.g. NASDAQ).",
        )

        # -------------------------------
        # Selective sync operations
        # -------------------------------
        parser.add_argument(
            "--profile",
            action="store_true",
            help="Sync only profile data.",
        )
        parser.add_argument(
            "--quote",
            action="store_true",
            help="Sync only price/quote data.",
        )
        parser.add_argument(
            "--dividends",
            action="store_true",
            help="Sync only dividend data.",
        )
        parser.add_argument(
            "--identifiers",
            action="store_true",
            help="Sync only identifier resolution (ticker, ISIN, CUSIP, CIK)."
        )

        # -------------------------------
        # Sync all components
        # -------------------------------
        parser.add_argument(
            "--all",
            action="store_true",
            help="Sync ALL components (profile, quote, dividends, identifiers)."
        )

        # -------------------------------
        # Dry run
        # -------------------------------
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do everything except saving DB changes.",
        )

    def handle(self, *args, **opts):

        asset_type_slug = opts["type"].strip()

        # Validate asset type
        try:
            asset_type = AssetType.objects.get(slug=asset_type_slug)
        except AssetType.DoesNotExist:
            raise CommandError(
                f"❌ AssetType '{asset_type_slug}' does not exist")

        # Get the correct sync service
        service = AssetSyncManager.for_type(asset_type_slug)
        if not service:
            raise CommandError(
                f"❌ No sync service implemented for type '{asset_type_slug}'")

        # -----------------------------------------------------
        # 1. UNIVERSE SYNC (optional)
        # -----------------------------------------------------
        if opts["include_universe"]:
            self.stdout.write(self.style.NOTICE("🔭 Running universe sync..."))
            results = service.sync_universe(
                exchange=opts.get("exchange"),
                dry_run=opts.get("dry_run")
            )
            self.stdout.write(self.style.SUCCESS(
                f"universe sync completed: {results}"
            ))

        # -----------------------------------------------------
        # 2. SINGLE ASSET TARGETED SYNC
        # -----------------------------------------------------
        symbol = opts.get("symbol")
        if symbol:
            symbol = symbol.upper().strip()

            # Look up the asset
            asset = (
                Asset.objects.filter(
                    asset_type=asset_type,
                    indentifier__id_type=AssetIdentifier.IdentifierType.TICKER,
                    identifiers__value=symbol,
                )
                .first()
            )

            if not asset:
                raise CommandError(f"❌ Asset {symbol} not found.")

            self.stdout.write(self.style.NOTICE(
                f"🔄 Syncing single asset: {symbol}"))

            # Determine which sync components to run
            service.sync_asset(
                asset,
                profile=opts["profile"] or opts["all"],
                quote=opts["quote"] or opts["all"],
                dividends=opts["dividends"] or opts["all"],
                identifiers=opts["identifiers"] or opts["all"],
            )

            self.stdout.write(self.style.SUCCESS(
                f"✅ Completed sync for {symbol}"))
            return

        # -----------------------------------------------------
        # 3. SYNC ALL ASSETS OF THIS TYPE (bulk deep sync)
        # -----------------------------------------------------
        self.stdout.write(self.style.NOTICE(
            f"🔄 Running deep sync for all '{asset_type_slug}' assets..."
        ))

        results = service.sync_all_assets(
            profile=opts["profile"] or opts["all"],
            quote=opts["quote"] or opts["all"],
            dividends=opts["dividends"] or opts["all"],
            identifiers=opts["identifiers"] or opts["all"],
            dry_run=opts["dry_run"],
        )

        self.stdout.write(self.style.SUCCESS(
            f"✅ Completed deep sync for {asset_type_slug}: {results}"
        ))
