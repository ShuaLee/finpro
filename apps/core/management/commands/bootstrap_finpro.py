from django.core.management.base import BaseCommand
from django.db import transaction

# --- AssetType + AccountType seeds ---
from assets.services.seeds.seed_asset_types import seed_asset_types
from accounts.services.seeds.account_seeder import seed_account_types

# --- Real Estate Types ---
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
    help = (
        "Full system bootstrap: AssetTypes, AccountTypes, countries, FX currencies, "
        "schema templates, formulas, and master constraints."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("\n🚀 Starting FinPro system bootstrap...\n"))

        # ============================================================
        # 0. Seed Asset Types
        # ============================================================
        self.stdout.write("🧩 Seeding system AssetTypes...")
        asset_count = seed_asset_types()
        self.stdout.write(self.style.SUCCESS(f"   ✔ AssetTypes seeded ({asset_count})\n"))

        # ============================================================
        # 1. Seed Account Types
        # ============================================================
        self.stdout.write("📦 Seeding system AccountTypes...")
        account_count = seed_account_types()
        self.stdout.write(self.style.SUCCESS(f"   ✔ AccountTypes seeded ({account_count})\n"))

        # ============================================================
        # 2. Sync Countries
        # ============================================================
        self.stdout.write("🌍 Syncing countries...")
        country_count = CountrySyncService.sync_countries()
        self.stdout.write(self.style.SUCCESS(f"   ✔ Countries synced ({country_count} updated)\n"))

        # ============================================================
        # 3. Sync FX Currencies
        # ============================================================
        self.stdout.write("💱 Syncing FX currencies...")
        fx_count = FXSyncService.sync_currencies()
        self.stdout.write(self.style.SUCCESS(f"   ✔ FX currencies synced ({fx_count} new)\n"))

        # ============================================================
        # 4. Skip FX Pairs
        # ============================================================
        self.stdout.write(self.style.WARNING("⚠ Skipping FX pair sync (lazy lookup instead)\n"))

        # ============================================================
        # 5. Schema Templates
        # ============================================================
        self.stdout.write("📐 Seeding schema templates...")

        self._seed_schema_template(EQUITY_TEMPLATE_CONFIG)
        self._seed_schema_template(CRYPTO_TEMPLATE_CONFIG)

        self.stdout.write(self.style.SUCCESS("   ✔ Schema templates seeded\n"))

        # ============================================================
        # 6. Formulas
        # ============================================================
        self.stdout.write("🧮 Seeding system formulas...")
        created, updated = self._seed_formulas()
        self.stdout.write(
            self.style.SUCCESS(
                f"   ✔ Formulas loaded ({created} created, {updated} updated)\n"
            )
        )

        # ============================================================
        # 7. Constraints
        # ============================================================
        self.stdout.write("📏 Seeding master constraints...")
        self._seed_constraints()
        self.stdout.write(self.style.SUCCESS("   ✔ Master constraints seeded\n"))

        # ============================================================
        # 8. Real Estate Subtypes
        # ============================================================
        self.stdout.write("🏠 Seeding real estate types...")
        re_count = seed_real_estate_types()
        self.stdout.write(self.style.SUCCESS(f"   ✔ Real estate types seeded ({re_count})\n"))

        # ============================================================
        # DONE
        # ============================================================
        self.stdout.write(self.style.SUCCESS("🎉 FinPro bootstrap complete!"))

    # ---------------------------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------------------------

    def _seed_schema_template(self, cfg):
        """
        Seed or update a schema template based on a config dict.
        Requires `account_type` in config to already be an AccountType instance.
        """

        # Ensure account_type is a real FK object, not a slug/string
        account_type = cfg["account_type"]
        if not hasattr(account_type, "pk"):
            raise ValueError(
                f"Schema template config has invalid account_type: {account_type}. "
                "Must be an AccountType instance."
            )

        template, _ = SchemaTemplate.objects.update_or_create(
            account_type=account_type,
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

            temp = Formula(expression=expression)
            deps = list(FormulaDependencyResolver(temp).extract_identifiers())

            formula, is_created = Formula.objects.get_or_create(
                identifier=identifier,
                defaults={
                    "title": data.get("title", identifier.replace("_", " ").title()),
                    "expression": expression,
                    "decimal_places": data.get("decimal_places"),
                    "dependencies": deps,
                    "is_system": True,
                },
            )

            if is_created:
                created += 1
                continue

            # Update existing record
            changed = False

            maybe_title = data.get("title", formula.title)
            if formula.title != maybe_title:
                formula.title = maybe_title
                changed = True

            if formula.expression != expression:
                formula.expression = expression
                changed = True

            if formula.decimal_places != data.get("decimal_places"):
                formula.decimal_places = data.get("decimal_places")
                changed = True

            if formula.dependencies != deps:
                formula.dependencies = deps
                changed = True

            if changed:
                formula.save()
                updated += 1

        return created, updated

    def _seed_constraints(self):
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
