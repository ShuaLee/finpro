from django.core.management.base import BaseCommand
from django.db import transaction

from apps.assets.models import AssetType


SYSTEM_ASSET_TYPES = [
    {"name": "Equity", "slug": "equity", "aliases": []},
    {"name": "Cryptocurrency", "slug": "crypto", "aliases": ["cryptocurrency"]},
    {"name": "Real Estate", "slug": "real_estate", "aliases": ["real-estate"]},
    {"name": "Precious Metal", "slug": "precious_metal", "aliases": ["precious-metal"]},
    {"name": "Commodity", "slug": "commodity", "aliases": []},
    {"name": "Private Equity", "slug": "private_equity", "aliases": ["private-equity"]},
    {"name": "Fund", "slug": "fund", "aliases": []},
    {"name": "Cash", "slug": "cash", "aliases": []},
    {"name": "Fixed Income", "slug": "fixed_income", "aliases": ["fixed-income", "bond"]},
    {"name": "Derivative", "slug": "derivative", "aliases": []},
    {"name": "Collectible", "slug": "collectible", "aliases": []},
    {"name": "Vehicle", "slug": "vehicle", "aliases": []},
    {"name": "Business Interest", "slug": "business_interest", "aliases": ["business-interest"]},
    {"name": "Insurance", "slug": "insurance", "aliases": []},
    {"name": "Other", "slug": "other", "aliases": []},
]


class Command(BaseCommand):
    help = "Seed common system asset types."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        updated = 0

        for spec in SYSTEM_ASSET_TYPES:
            name = spec["name"]
            slug = spec["slug"]
            aliases = spec["aliases"]

            asset_type = (
                AssetType.objects.filter(created_by__isnull=True, slug__in=[slug, *aliases]).first()
                or AssetType.objects.filter(created_by__isnull=True, name=name).first()
            )

            if not asset_type:
                AssetType.objects.create(
                    name=name,
                    created_by=None,
                    description="",
                )
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created system asset type: {name}"))
                continue

            changed = []

            if asset_type.name != name:
                asset_type.name = name
                changed.append("name")

            if asset_type.slug != slug:
                asset_type.slug = slug
                changed.append("slug")

            if asset_type.created_by is not None:
                asset_type.created_by = None
                changed.append("created_by")

            if changed:
                asset_type.save(update_fields=changed)
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Updated system asset type: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Exists: {name}"))

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"System asset types seeded. Created={created}, Updated={updated}"
            )
        )
