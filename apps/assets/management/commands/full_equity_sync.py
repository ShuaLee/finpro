from django.core.management.base import BaseCommand, CommandError

from assets.models.equity import EquityAsset, EquitySnapshotID
from assets.services.equity.equity_profile_sync import EquityProfileSyncService
from assets.services.equity.equity_price_sync import EquityPriceSyncService


class Command(BaseCommand):
    help = (
        "Sync equity profile data and/or latest price for a single ticker "
        "(active snapshot only)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "ticker",
            type=str,
            help="Equity ticker symbol (e.g. AAPL, MSFT)",
        )

        parser.add_argument(
            "--profile-only",
            action="store_true",
            help="Only sync equity profile data",
        )

        parser.add_argument(
            "--price-only",
            action="store_true",
            help="Only sync equity price data",
        )

        parser.add_argument(
            "--no-fail-price",
            action="store_true",
            help="Do not fail the command if price sync updates nothing",
        )

    def handle(self, *args, **options):
        ticker = options["ticker"].upper().strip()
        profile_only = options["profile_only"]
        price_only = options["price_only"]
        no_fail_price = options["no_fail_price"]

        if profile_only and price_only:
            raise CommandError(
                "Cannot use --profile-only and --price-only together."
            )

        # -------------------------------------------------
        # Resolve active snapshot
        # -------------------------------------------------
        try:
            snapshot = EquitySnapshotID.objects.get(id=1).current_snapshot
        except EquitySnapshotID.DoesNotExist:
            raise CommandError("EquitySnapshotID with id=1 does not exist.")

        # -------------------------------------------------
        # Resolve equity asset (needed for profile sync)
        # -------------------------------------------------
        equity = None
        if not price_only:
            try:
                equity = EquityAsset.objects.get(
                    ticker=ticker,
                    snapshot_id=snapshot,
                )
            except EquityAsset.DoesNotExist:
                raise CommandError(
                    f"Ticker '{ticker}' not found in active snapshot."
                )

        # -------------------------------------------------
        # 1️⃣ Profile sync (default: YES)
        # -------------------------------------------------
        if not price_only:
            self.stdout.write(f"🔄 Syncing profile for {ticker}...")

            profile_service = EquityProfileSyncService()
            profile_result = profile_service.sync(equity)

            self.stdout.write(
                self.style.SUCCESS("✅ Profile sync complete")
            )
            self.stdout.write(str(profile_result))

        # -------------------------------------------------
        # 2️⃣ Price sync (default: YES)
        # -------------------------------------------------
        if not profile_only:
            self.stdout.write(f"💰 Syncing price for {ticker}...")

            price_service = EquityPriceSyncService()
            price_result = price_service.run(ticker=ticker)

            if price_result.get("updated", 0) == 0 and not no_fail_price:
                raise CommandError(
                    f"No price updated for {ticker}"
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Price synced for {ticker}"
                )
            )

        # -------------------------------------------------
        # Done
        # -------------------------------------------------
        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 Sync completed successfully for {ticker}"
            )
        )
