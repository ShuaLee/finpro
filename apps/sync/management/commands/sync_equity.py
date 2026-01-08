# sync/management/commands/sync_equity.py
from django.core.management.base import BaseCommand

from assets.models.asset_core import Asset
from sync.services.asset_manager import AssetSyncManager


class Command(BaseCommand):
    help = "Sync a single equity by ticker"

    def add_arguments(self, parser):
        parser.add_argument("ticker")
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **opts):
        ticker = opts["ticker"].upper()

        asset = Asset.objects.filter(
            identifiers__id_type="TICKER",
            identifiers__value=ticker,
        ).distinct().first()

        if not asset:
            self.stderr.write(f"Ticker {ticker} not found")
            return

        result = AssetSyncManager.sync_asset(asset, force=opts["force"])
        self.stdout.write(self.style.SUCCESS("Sync complete"))
