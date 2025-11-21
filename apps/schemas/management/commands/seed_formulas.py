from django.core.management.base import BaseCommand
from django.db import transaction

from schemas.config.formulas.formula_template import FORMULA_TEMPLATE
from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver


class Command(BaseCommand):
    help = "Loads or updates built-in system formulas from FORMULA_TEMPLATE."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        updated = 0

        for key, data in FORMULA_TEMPLATE.items():
            identifier = data["identifier"]

            # Auto-extract dependencies from expression
            expr = data["expression"]
            temp_formula = Formula(expression=expr)
            raw_deps = FormulaDependencyResolver(
                temp_formula).extract_identifiers()
            deps = list(map(str, raw_deps))

            formula, exists = Formula.objects.get_or_create(
                identifier=identifier,
                defaults={
                    "title": data.get("title", identifier.replace("_", " ").title()),
                    "expression": expr,
                    "dependencies": deps,
                    "decimal_places": data.get("decimal_places"),
                    "is_system": True,
                }
            )

            # Update fields
            new_title = data.get("title", formula.title)
            new_expr = data.get("expression", formula.expression)
            new_dp = data.get("decimal_places", formula.decimal_places)

            changed = False

            if formula.title != new_title:
                formula.title = new_title
                changed = True

            if formula.expression != new_expr:
                formula.expression = new_expr
                changed = True

            if formula.decimal_places != new_dp:
                formula.decimal_places = new_dp
                changed = True

            # ALWAYS update dependencies automatically
            if formula.dependencies != deps:
                formula.dependencies = deps
                changed = True

            # System formulas must always be system
            if formula.is_system is not True:
                formula.is_system = True
                changed = True

            if changed and exists:
                formula.save()
                updated += 1
            elif not exists:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"System formulas loaded: {created} created, {updated} updated."
        ))
