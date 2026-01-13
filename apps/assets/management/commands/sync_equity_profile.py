from django.core.management.base import BaseCommand, CommandError

from assets.models.equity import EquityAsset, EquitySnapshotID
from assets.services.equity.equity_profile_sync import EquityProfileSyncService


class Command(BaseCommand):
    help = "Sync equity profile data from FMP for a single ticker"

    def add_arguments(self, parser):
        parser.add_argument(
            "ticker",
            type=str,
            help="Equity ticker to sync (e.g. AAPL)",
        )

    def handle(self, *args, **options):
        ticker = options["ticker"].upper().strip()

        snapshot = EquitySnapshotID.objects.get(id=1).current_snapshot

        try:
            equity = EquityAsset.objects.get(
                ticker=ticker,
                snapshot_id=snapshot,
            )
        except EquityAsset.DoesNotExist:
            raise CommandError(
                f"Ticker '{ticker}' not found in active snapshot."
            )

        self.stdout.write(f"🔄 Syncing profile for {ticker}...")

        service = EquityProfileSyncService()
        result = service.sync(equity)

        self.stdout.write(self.style.SUCCESS("✅ Profile sync complete"))
        self.stdout.write(str(result))
