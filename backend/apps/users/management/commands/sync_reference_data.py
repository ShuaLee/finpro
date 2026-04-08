from django.core.management.base import BaseCommand

from apps.users.services import ReferenceDataService


class Command(BaseCommand):
    help = "Sync supported country and currency reference data from FMP."

    def add_arguments(self, parser):
        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            help="Deactivate local rows that no longer appear in the provider response.",
        )

    def handle(self, *args, **options):
        deactivate_missing = options["deactivate_missing"]
        country_result = ReferenceDataService.sync_supported_countries(
            deactivate_missing=deactivate_missing
        )
        currency_result = ReferenceDataService.sync_supported_currencies(
            deactivate_missing=deactivate_missing
        )
        self.stdout.write(
            self.style.SUCCESS(
                str(
                    {
                        "countries": country_result,
                        "currencies": currency_result,
                    }
                )
            )
        )
