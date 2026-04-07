from django.core.management.base import BaseCommand

from apps.integrations.services import EquityDirectorySyncService


class Command(BaseCommand):
    help = "Rebuild the active FMP equity directory snapshot."

    def handle(self, *args, **options):
        result = EquityDirectorySyncService.rebuild_from_fmp()
        self.stdout.write(self.style.SUCCESS(str(result)))
