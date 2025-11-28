from django.core.management.base import BaseCommand
from fx.services.country_sync import CountrySyncService


class Command(BaseCommand):
    help = "Sync country list from FMP and enrich using pycountry."

    def handle(self, *args, **options):
        count = CountrySyncService.sync_countries()
        self.stdout.write(
            self.style.SUCCESS(f"✔ Country sync complete ({count} updated)")
        )
