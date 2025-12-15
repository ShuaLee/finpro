from django.core.management.base import BaseCommand
from assets.services.syncs.equity_sync import EquitySyncService


class Command(BaseCommand):
    help = "Sync all equity profiles using FMP bulk profile API (across all parts)."

    def handle(self, *args, **options):
        results = EquitySyncService.sync_profiles_bulk()
        self.stdout.write(
            self.style.SUCCESS(f"Equity profile bulk sync complete: {results}")
        )
