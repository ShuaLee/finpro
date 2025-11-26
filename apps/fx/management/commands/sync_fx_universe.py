from django.core.management.base import BaseCommand

from fx.services.sync import FXSyncService


class Command(BaseCommand):
    help = "Sync full FX universe (currencies + all known pairs from FMP)."

    def handle(self, *args, **options):
        self.stdout.write("Fetching FX currency universe...")

        created = FXSyncService.sync_currencies()

        self.stdout.write(
            self.style.SUCCESS(
                f"FX Universe sync complete. {created} new currencies added."
            )
        )
