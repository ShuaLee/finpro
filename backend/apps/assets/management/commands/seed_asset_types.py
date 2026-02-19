from django.core.management.base import BaseCommand
from django.db import transaction

from assets.models.core import AssetType


SYSTEM_ASSET_TYPES = [
    {"name": "Equity", "slug": "equity", "aliases": []},
    {"name": "Cryptocurrency", "slug": "crypto", "aliases": ["cryptocurrency"]},
    {"name": "Commodity", "slug": "commodity", "aliases": []},
    {"name": "Precious Metal", "slug": "precious_metal", "aliases": ["precious-metal"]},
    {"name": "Real Estate", "slug": "real_estate", "aliases": ["real-estate"]},
]


class Command(BaseCommand):
    help = "Initialize system AssetTypes with canonical code-safe slugs."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        updated = 0

        for spec in SYSTEM_ASSET_TYPES:
            name = spec["name"]
            slug = spec["slug"]
            aliases = spec["aliases"]

            obj = (
                AssetType.objects.filter(created_by=None, slug__in=[slug, *aliases]).first()
                or AssetType.objects.filter(created_by=None, name=name).first()
            )

            if not obj:
                AssetType.objects.create(
                    name=name,
                    slug=slug,
                    created_by=None,
                )
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created system AssetType: {name} ({slug})")
                )
                continue

            changed = []
            if obj.name != name:
                obj.name = name
                changed.append("name")
            if obj.slug != slug:
                obj.slug = slug
                changed.append("slug")
            if obj.created_by_id is not None:
                obj.created_by = None
                changed.append("created_by")

            if changed:
                obj.save(update_fields=changed)
                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Updated system AssetType: {name} ({slug})")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Exists: {name} ({slug})")
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"System AssetTypes initialized. Created={created}, Updated={updated}"
            )
        )
