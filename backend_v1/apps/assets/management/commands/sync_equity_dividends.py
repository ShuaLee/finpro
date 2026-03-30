from django.core.management.base import BaseCommand, CommandError

from assets.models.equity import EquityAsset, EquitySnapshotID
from assets.services.equity.dividend_sync import EquityDividendSyncService



class Command(BaseCommand):
    help = "Sync dividend snapshot for a single equity (active snapshot only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "ticker",
            type=str,
            help="Equity ticker symbol (e.g. AAPL)",
        )

    def handle(self, *args, **options):
        ticker = options["ticker"].upper().strip()

        snapshot = EquitySnapshotID.objects.get(id=1).current_snapshot

        equity = EquityAsset.objects.filter(
            snapshot_id=snapshot,
            ticker__iexact=ticker,
        ).select_related("asset").first()

        if not equity:
            raise CommandError(f"Equity {ticker} not found in active snapshot")

        self.stdout.write(f"💸 Syncing dividends for {ticker}...")

        EquityDividendSyncService().sync(equity.asset)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Dividend snapshot updated for {ticker}")
        )
