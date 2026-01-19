from django.core.management.base import BaseCommand
from django.db import transaction

from schemas.models.constraints import MasterConstraint


CONSTRAINT_TEMPLATES = {
    "string": [
        {
            "name": "max_length",
            "label": "Max Length",
            "default": "100",
            "min": "1",
            "max": "255",
            "editable": False,
        },
    ],
    "decimal": [
        {
            "name": "decimal_places",
            "label": "Decimal Places",
            "default": "4",
            "min": "0",
            "max": "20",
            "editable": True,
        },
        {
            "name": "max_value",
            "label": "Maximum Value",
            "default": None,
            "min": None,
            "max": None,
            "editable": False,
        },
        {
            "name": "min_value",
            "label": "Minimum Value",
            "default": None,
            "min": None,
            "max": None,
            "editable": False,
        },
    ],
    "integer": [
        {
            "name": "max_value",
            "label": "Maximum Value",
            "default": None,
            "min": None,
            "max": None,
            "editable": False,
        },
        {
            "name": "min_value",
            "label": "Minimum Value",
            "default": None,
            "min": None,
            "max": None,
            "editable": False,
        },
    ],
    "date": [
        {
            "name": "min_date",
            "label": "Earliest Date",
            "default": None,
            "min": None,
            "max": None,
            "editable": False,
        },
        {
            "name": "max_date",
            "label": "Latest Date",
            "default": None,
            "min": None,
            "max": None,
            "editable": False,
        },
    ],
    "boolean": [],
    "url": [
        {
            "name": "max_length",
            "label": "Max Length",
            "default": "200",
            "min": "1",
            "max": "500",
            "editable": False,
        },
    ],
}


class Command(BaseCommand):
    help = "Seed MasterConstraint definitions used by SchemaColumns"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding MasterConstraints...")

        created = 0
        skipped = 0

        for applies_to, rules in CONSTRAINT_TEMPLATES.items():
            for rule in rules:
                obj, was_created = MasterConstraint.objects.get_or_create(
                    applies_to=applies_to,
                    name=rule["name"],
                    defaults={
                        "label": rule["label"],
                        "default_value": rule.get("default"),
                        "min_limit": rule.get("min"),
                        "max_limit": rule.get("max"),
                        "is_editable": rule.get("editable", True),
                        "is_active": True,
                    },
                )
                if was_created:
                    created += 1
                    self.stdout.write(f"  ✅ Created [{applies_to}] {obj.name}")
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Done. Created: {created}, Skipped: {skipped}"
        ))
