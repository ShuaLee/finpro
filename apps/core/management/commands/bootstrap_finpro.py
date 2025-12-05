from django.core.management.base import BaseCommand
from django.db import transaction

# --- Assets ---
from assets.services.seeds.seed_asset_types import _seed_asset_types
from assets.services.seeds.seed_real_estate_types import seed_real_estate_types

# --- FX + Countries ---
from fx.services.sync import FXSyncService
from fx.services.country_sync import CountrySyncService

# --- Schema Templates ---
from schemas.config.schema_templates.equity_template import EQUITY_TEMPLATE_CONFIG
from schemas.config.schema_templates.crypto_template import CRYPTO_TEMPLATE_CONFIG
from schemas.models.template import SchemaTemplate, SchemaTemplateColumn

# --- Formulas ---
from schemas.config.formulas.formula_template import FORMULA_TEMPLATE
from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver

# --- Constraints ---
from schemas.config.constraints_template import CONSTRAINT_TEMPLATES
from schemas.models.constraints import MasterConstraint


class Command(BaseCommand):
    help = "Full system bootstrap: countries, FX currencies, templates, formulas, constraints."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "🚀 Starting FinPro system bootstrap...\n"))

        self.stdout.write(self.style.WARNING(
            "🚀 Starting FinPro system bootstrap...\n"))

        # ============================================================
        # 0. Sync AssetTypes
        # ============================================================
        self.stdout.write("🧩 Seeding system AssetTypes...")
        count = _seed_asset_types()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ AssetTypes seeded ({count})\n"))

        # ============================================================
        # 1. Sync Countries
        # ============================================================
        self.stdout.write("🌍 Syncing countries...")
        country_count = CountrySyncService.sync_countries()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ Countries synced ({country_count} updated)\n"))

        # ============================================================
        # 2. Sync FX Currencies
        # ============================================================
        self.stdout.write("💱 Syncing FX currencies...")
        fx_count = FXSyncService.sync_currencies()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ FX currencies synced ({fx_count} new)\n"))

        # ============================================================
        # 3. (Removed) FX pairs – DO NOT SYNC HERE
        # ============================================================
        self.stdout.write(self.style.WARNING(
            "⚠ Skipping FX pair sync (lazy lookup used instead)\n"))

        # ============================================================
        # 4. Schema Templates (Equity, Crypto, more later)
        # ============================================================
        self.stdout.write("📐 Seeding schema templates...")

        self._seed_schema_template(EQUITY_TEMPLATE_CONFIG)
        self._seed_schema_template(CRYPTO_TEMPLATE_CONFIG)

        self.stdout.write(self.style.SUCCESS("   ✔ Schema templates seeded\n"))

        # ============================================================
        # 5. Formulas
        # ============================================================
        self.stdout.write("🧮 Seeding system formulas...")
        created, updated = self._seed_formulas()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ Formulas loaded ({created} created, {updated} updated)\n"
        ))

        # ============================================================
        # 6. Constraints
        # ============================================================
        self.stdout.write("📏 Seeding master constraints...")
        self._seed_constraints()
        self.stdout.write(self.style.SUCCESS(
            "   ✔ Master constraints seeded\n"))

        # ============================================================
        # 7. Real Estate Types
        # ============================================================
        self.stdout.write("🏠 Seeding real estate types...")
        re_count = seed_real_estate_types()
        self.stdout.write(self.style.SUCCESS(
            f"   ✔ Real estate types seeded ({re_count})\n"
        ))

        # ============================================================
        # Done
        # ============================================================
        self.stdout.write(self.style.SUCCESS("🎉 FinPro bootstrap complete!"))

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _seed_schema_template(self, cfg):
        """Seed or update a schema template based on a config block."""
        template, _ = SchemaTemplate.objects.update_or_create(
            account_type=cfg["account_type"],
            defaults={
                "name": cfg["name"],
                "description": cfg["description"],
                "is_active": True,
            },
        )

        for col in cfg["columns"]:
            SchemaTemplateColumn.objects.update_or_create(
                template=template,
                identifier=col["identifier"],
                defaults={
                    "title": col["title"],
                    "data_type": col["data_type"],
                    "source": col["source"],
                    "source_field": col["source_field"],
                    "is_editable": col["is_editable"],
                    "is_system": col["is_system"],
                    "is_deletable": col.get("is_deletable", True),
                    "is_default": col.get("is_default", False),
                    "display_order": col.get("display_order"),
                    "constraints": col.get("constraints", {}),
                },
            )

    def _seed_formulas(self):
        created = 0
        updated = 0

        for key, data in FORMULA_TEMPLATE.items():
            identifier = data["identifier"]
            expression = data["expression"]

            # Extract dependencies
            temp_formula = Formula(expression=expression)
            deps = list(map(str, FormulaDependencyResolver(
                temp_formula).extract_identifiers()))

            formula, was_created = Formula.objects.get_or_create(
                identifier=identifier,
                defaults={
                    "title": data.get("title", identifier.replace("_", " ").title()),
                    "expression": expression,
                    "decimal_places": data.get("decimal_places"),
                    "dependencies": deps,
                    "is_system": True,
                }
            )

            if was_created:
                created += 1
                continue  # nothing else to update

            # Otherwise check for updates
            changed = False

            new_title = data.get("title", formula.title)
            new_expr = expression
            new_dp = data.get("decimal_places")
            new_deps = deps

            if formula.title != new_title:
                formula.title = new_title
                changed = True

            if formula.expression != new_expr:
                formula.expression = new_expr
                changed = True

            if formula.decimal_places != new_dp:
                formula.decimal_places = new_dp
                changed = True

            if formula.dependencies != new_deps:
                formula.dependencies = new_deps
                changed = True

            if changed:
                formula.save()
                updated += 1

        return created, updated

    def _seed_constraints(self):
        """Seed master constraint definitions."""
        for data_type, templates in CONSTRAINT_TEMPLATES.items():
            for t in templates:
                MasterConstraint.objects.update_or_create(
                    applies_to=data_type,
                    name=t["name"],
                    defaults={
                        "label": t["label"],
                        "default_value": t.get("default"),
                        "min_limit": t.get("min"),
                        "max_limit": t.get("max"),
                        "is_editable": t.get("editable", True),
                        "is_active": True,
                    },
                )
