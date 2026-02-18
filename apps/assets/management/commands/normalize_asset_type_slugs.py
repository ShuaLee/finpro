from django.core.management.base import BaseCommand
from django.db import transaction

from assets.models.core import AssetType


CANONICAL_SYSTEM_TYPES = {
    "Equity": "equity",
    "Cryptocurrency": "crypto",
    "Commodity": "commodity",
    "Precious Metal": "precious_metal",
    "Real Estate": "real_estate",
}


class Command(BaseCommand):
    help = "Normalize system AssetType slugs to canonical code-safe values."

    @transaction.atomic
    def handle(self, *args, **options):
        updated = 0

        for name, canonical_slug in CANONICAL_SYSTEM_TYPES.items():
            obj = AssetType.objects.filter(created_by=None, name=name).first()
            if not obj:
                self.stdout.write(self.style.WARNING(f"Missing system type: {name}"))
                continue

            if obj.slug != canonical_slug:
                obj.slug = canonical_slug
                obj.save(update_fields=["slug"])
                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated slug for {name}: {canonical_slug}"
                    )
                )
            else:
                self.stdout.write(f"OK: {name} ({canonical_slug})")

        self.stdout.write(
            self.style.SUCCESS(f"AssetType slug normalization complete. Updated={updated}")
        )
