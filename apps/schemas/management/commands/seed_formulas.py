from django.core.management.base import BaseCommand
from django.db import transaction

from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver


FORMULAS = [
    {
        "identifier": "current_value_asset_fx",
        "title": "Current Value – Asset FX",
        "expression": "quantity * last_price",
        "decimal_places": 2,
    },
    {
        "identifier": "current_value_profile_fx",
        "title": "Current Value – Profile FX",
        "expression": "quantity * last_price",
        "decimal_places": 2,
    },
]


class Command(BaseCommand):
    help = "Seed built-in system formulas (no config files used)."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        updated = 0

        for data in FORMULAS:
            identifier = data["identifier"]
            expr = data["expression"]
            deps = FormulaDependencyResolver(Formula(expression=expr)).extract_identifiers()

            obj, was_created = Formula.objects.update_or_create(
                identifier=identifier,
                defaults={
                    "title": data["title"],
                    "expression": expr,
                    "dependencies": list(map(str, deps)),
                    "decimal_places": data.get("decimal_places"),
                    "is_system": True,
                }
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Formulas seeded: {created} created, {updated} updated"
        ))
