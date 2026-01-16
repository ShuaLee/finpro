from django.core.management.base import BaseCommand
from django.db import transaction

from assets.models.core import AssetType


SYSTEM_ASSET_TYPES = [
    "Equity",
    "Cryptocurrency",
    "Commodity",
    "Precious Metal",
    "Real Estate",
]


class Command(BaseCommand):
    help = "Initialize system AssetTypes (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        existing = 0

        for name in SYSTEM_ASSET_TYPES:
            obj, was_created = AssetType.objects.get_or_create(
                name=name,
                created_by=None,  # 🔒 system-owned
                defaults={},
            )

            if was_created:
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created system AssetType: {name}")
                )
            else:
                existing += 1
                self.stdout.write(
                    self.style.WARNING(f"Exists: {name}")
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"System AssetTypes initialized. "
                f"Created={created}, Existing={existing}"
            )
        )
