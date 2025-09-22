from django.core.management.base import BaseCommand
from assets.services.syncs.equity_sync import EquitySyncService


class Command(BaseCommand):
    help = "Sync equities in DB against FMP /stock/list"

    def handle(self, *args, **options):
        results = EquitySyncService.sync_universe()
        self.stdout.write(self.style.SUCCESS(
            f"Equity universe sync: {results}"))
