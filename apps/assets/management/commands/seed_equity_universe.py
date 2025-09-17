from django.core.management.base import BaseCommand
from assets.services.universe.equity_universe import seed_equity_universe


class Command(BaseCommand):
    help = "Bootstrap the DB with the full equity universe from FMP (one-time use)."

    def handle(self, *args, **options):
        results = seed_equity_universe()
        self.stdout.write(self.style.SUCCESS(
            f"Equity universe seeded: {results}"))
