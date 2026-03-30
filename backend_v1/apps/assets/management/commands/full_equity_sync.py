from django.core.management.base import BaseCommand, CommandError

from assets.models.equity import EquityAsset, EquitySnapshotID
from assets.services.equity.dividend_sync import EquityDividendSyncService
from assets.services.equity.equity_price_sync import EquityPriceSyncService
from assets.services.equity.equity_profile_sync import EquityProfileSyncService


class Command(BaseCommand):
    help = "Run profile, price, and dividend sync for active-snapshot equities."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ticker",
            type=str,
            help="Optional single ticker (e.g. AAPL). If omitted, syncs all active equities.",
        )
        parser.add_argument(
            "--skip-profile",
            action="store_true",
            help="Skip profile sync.",
        )
        parser.add_argument(
            "--skip-price",
            action="store_true",
            help="Skip price sync.",
        )
        parser.add_argument(
            "--skip-dividends",
            action="store_true",
            help="Skip dividend sync.",
        )

    def handle(self, *args, **options):
        try:
            snapshot = EquitySnapshotID.objects.get(id=1).current_snapshot
        except EquitySnapshotID.DoesNotExist as exc:
            raise CommandError("EquitySnapshotID with id=1 does not exist.") from exc

        ticker = (options.get("ticker") or "").upper().strip()
        skip_profile = options["skip_profile"]
        skip_price = options["skip_price"]
        skip_dividends = options["skip_dividends"]

        if skip_profile and skip_price and skip_dividends:
            raise CommandError("Nothing to do: all sync steps are disabled.")

        equities = EquityAsset.objects.filter(snapshot_id=snapshot).select_related("asset")
        if ticker:
            equities = equities.filter(ticker__iexact=ticker)

        equities = list(equities.order_by("ticker"))
        if not equities:
            raise CommandError("No equities found for the requested scope.")

        profile_service = EquityProfileSyncService()
        price_service = EquityPriceSyncService()
        dividend_service = EquityDividendSyncService()

        profile_synced = 0
        profile_failed = 0
        dividend_synced = 0
        dividend_failed = 0

        if not skip_profile:
            self.stdout.write("Syncing equity profiles...")
            for equity in equities:
                try:
                    profile_service.sync(equity)
                    profile_synced += 1
                except Exception:
                    profile_failed += 1

        if not skip_price:
            self.stdout.write("Syncing equity prices...")
            price_result = price_service.run(ticker=ticker or None)
        else:
            price_result = {"updated": 0, "skipped": len(equities)}

        if not skip_dividends:
            self.stdout.write("Syncing equity dividends...")
            for equity in equities:
                try:
                    dividend_service.sync(equity.asset)
                    dividend_synced += 1
                except Exception:
                    dividend_failed += 1

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Full equity sync complete | "
                    f"profiles ok={profile_synced} failed={profile_failed} | "
                    f"prices updated={price_result['updated']} skipped={price_result['skipped']} | "
                    f"dividends ok={dividend_synced} failed={dividend_failed}"
                )
            )
        )
