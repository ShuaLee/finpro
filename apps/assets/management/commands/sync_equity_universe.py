from django.core.management.base import BaseCommand
from assets.services.universe.equity_universe import sync_equity_universe


class Command(BaseCommand):
    help = "Sync equities in DB against FMP /stock/list"

    def handle(self, *args, **options):
        results = sync_equity_universe()
        self.stdout.write(self.style.SUCCESS(
            f"Equity universe sync: {results}"))
