import json

from django.core.management.base import BaseCommand, CommandError

from assets.models.asset_core import Asset, AssetIdentifier, AssetType
from assets.services.syncs.equity import EquitySyncManager


class Command(BaseCommand):
    help = (
        "Seed or sync equity data.\n\n"
        "Modes:\n"
        "  --seed-db     Initial seed from FMP stock-list only\n"
        "  --universe    Repair / update existing equity universe\n"
        "  --symbol XYZ  Sync a single equity"
    )

    def add_arguments(self, parser):
        # ------------------------------------------------------------
        # MODES
        # ------------------------------------------------------------
        parser.add_argument(
            "--seed-db",
            action="store_true",
            help="Initial seed of equity universe (stock-list only)."
        )

        parser.add_argument(
            "--universe",
            action="store_true",
            help="Run full equity universe sync from FMP stock-list."
        )

        parser.add_argument(
            "--symbol",
            type=str,
            help="Sync a single equity by ticker (e.g. --symbol AAPL)"
        )

        # ------------------------------------------------------------
        # OPTIONS
        # ------------------------------------------------------------
        parser.add_argument(
            "--components",
            nargs="*",
            choices=["identifiers", "profile", "price", "dividends"],
            help="Optional list of components to sync. Default = all."
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform universe sync without DB modifications."
        )

        parser.add_argument(
            "--json",
            action="store_true",
            help="Output full structured sync results as JSON."
        )

    def handle(self, *args, **options):

        # ============================================================
        # 0. SEED DATABASE (ONE-TIME OPERATION)
        # ============================================================
        if options["seed_db"]:
            self.stdout.write(
                "🌱 Seeding equity universe from FMP stock-list...")

            results = EquitySyncManager.seed_universe()

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Seed complete: {results['created']} equities created"
                )
            )
            return

        # ============================================================
        # 1. UNIVERSE SYNC (REPAIR / MAINTENANCE)
        # ============================================================
        if options["universe"]:
            dry = options["dry_run"]
            self.stdout.write(
                f"🔄 Running equity universe sync (dry={dry})..."
            )

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
                    "AssetType slug='equity' not found. Run bootstrap."
                )

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
                    f"No equity found with ticker '{symbol}'."
                )

            components = options.get("components")

            self.stdout.write(
                f"🔄 Syncing equity {symbol} ({asset.name}) "
                f"components={components or 'ALL'}"
            )

            results = EquitySyncManager.sync(asset, components=components)

            # --------------------------------------------------------
            # JSON OUTPUT
            # --------------------------------------------------------
            if options["json"]:
                self.stdout.write(
                    json.dumps(results, indent=2, default=str)
                )
                return

            # --------------------------------------------------------
            # HUMAN OUTPUT
            # --------------------------------------------------------
            ok_count = 0
            self.stdout.write(self.style.SUCCESS("✅ Sync complete:"))

            for name, result in results.items():
                if result.get("success"):
                    ok_count += 1
                    stats = result.get("fields") or result.get("events")
                    if isinstance(stats, dict) and stats:
                        self.stdout.write(f" • {name}: ok {stats}")
                    else:
                        self.stdout.write(f" • {name}: ok")
                else:
                    error = result.get("error") or "unknown_error"
                    self.stdout.write(
                        self.style.ERROR(
                            f" • {name}: failed ({error})"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✔️ {ok_count}/{len(results)} components completed successfully"
                )
            )
            return

        # ============================================================
        # 3. NO VALID ARGUMENTS
        # ============================================================
        raise CommandError(
            "You must pass one of:\n"
            "  --seed-db\n"
            "  --universe\n"
            "  --symbol SYMBOL\n\n"
            "Examples:\n"
            "  manage.py sync_equities --seed-db\n"
            "  manage.py sync_equities --universe\n"
            "  manage.py sync_equities --symbol AAPL\n"
        )
