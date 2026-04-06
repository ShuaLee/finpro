from django.core.management.base import BaseCommand

from apps.assets.services import PublicAssetSyncService


class Command(BaseCommand):
    help = "Sync the public equity directory from FMP stock-list and actively-trading-list."

    def handle(self, *args, **options):
        result = PublicAssetSyncService.sync_equity_directory()
        self.stdout.write(self.style.SUCCESS(str(result)))
