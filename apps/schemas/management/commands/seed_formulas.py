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

            obj, exists = Formula.objects.get_or_create(
                identifier=identifier,
                defaults={
                    "title": data["title"],
                    "expression": expr,
                    "dependencies": list(map(str, deps)),
                    "decimal_places": data.get("decimal_places"),
                    "is_system": True,
                }
            )

            changed = False

            if not exists:
                created += 1
                continue

            if obj.expression != expr:
                obj.expression = expr
                changed = True

            if obj.title != data["title"]:
                obj.title = data["title"]
                changed = True

            if obj.decimal_places != data.get("decimal_places"):
                obj.decimal_places = data.get("decimal_places")
                changed = True

            new_deps = list(map(str, deps))
            if obj.dependencies != new_deps:
                obj.dependencies = new_deps
                changed = True

            if obj.is_system is not True:
                obj.is_system = True
                changed = True

            if changed:
                obj.save()
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Formulas seeded: {created} created, {updated} updated"
        ))
