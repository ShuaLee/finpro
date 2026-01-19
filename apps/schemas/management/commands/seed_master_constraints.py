from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from schemas.models.constraints import MasterConstraint


CONSTRAINT_TEMPLATES = {
    "string": [
        {
            "name": "max_length",
            "label": "Max Length",
            "default_string": "100",
        },
    ],
    "decimal": [
        {
            "name": "decimal_places",
            "label": "Decimal Places",
            "default_integer": 4,
        },
        {
            "name": "min_value",
            "label": "Minimum Value",
        },
        {
            "name": "max_value",
            "label": "Maximum Value",
        },
    ],
    "integer": [
        {
            "name": "min_value",
            "label": "Minimum Value",
        },
        {
            "name": "max_value",
            "label": "Maximum Value",
        },
    ],
    "date": [
        {
            "name": "min_date",
            "label": "Earliest Date",
        },
        {
            "name": "max_date",
            "label": "Latest Date",
        },
    ],
    "boolean": [],
    "url": [
        {
            "name": "max_length",
            "label": "Max Length",
            "default_string": "200",
        },
    ],
}


class Command(BaseCommand):
    help = "Seed MasterConstraint definitions using valid typed fields only"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding MasterConstraints (typed)…")

        created = 0
        updated = 0

        for applies_to, rules in CONSTRAINT_TEMPLATES.items():
            for rule in rules:
                defaults = {
                    "label": rule["label"],
                }

                # Write typed default fields only
                if "default_string" in rule:
                    defaults["default_string"] = rule["default_string"]

                if "default_integer" in rule:
                    defaults["default_integer"] = rule["default_integer"]

                if "default_decimal" in rule:
                    defaults["default_decimal"] = Decimal(str(rule["default_decimal"]))

                # 🚫 DO NOT include min_integer / max_integer

                obj, was_created = MasterConstraint.objects.update_or_create(
                    applies_to=applies_to,
                    name=rule["name"],
                    defaults=defaults,
                )

                if was_created:
                    created += 1
                    self.stdout.write(f"  ✅ Created [{applies_to}] {obj.name}")
                else:
                    updated += 1
                    self.stdout.write(f"  🔁 Updated [{applies_to}] {obj.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ MasterConstraints complete (created={created}, updated={updated})"
            )
        )
