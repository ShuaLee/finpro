from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal

from schemas.models import SchemaColumnTemplate
from schemas.config import SCHEMA_CONFIG_REGISTRY
from schemas.config.schema_registry.utils import validate_constraints
from formulas.models import Formula
from formulas.config.formula_registry.formulas import FORMULAS_REGISTRY


def convert_decimal(obj):
    """Recursively convert Decimals to floats so they serialize safely."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(v) for v in obj]
    return obj


class Command(BaseCommand):
    help = "Load schema column templates (and related formulas) into the DB"

    def handle(self, *args, **kwargs):
        template_created, template_updated, template_skipped = 0, 0, 0
        formula_created, formula_updated = 0, 0

        for schema_type, variant_map in SCHEMA_CONFIG_REGISTRY.items():
            for account_model, fields in variant_map.items():
                account_model_ct = ContentType.objects.get_for_model(account_model)

                for source, columns in fields.items():
                    for source_field, meta in columns.items():
                        try:
                            validate_constraints(
                                meta["data_type"],
                                convert_decimal(meta.get("constraints", {})),
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"❌ Constraint validation failed for {source_field}: {e}"
                                )
                            )
                            template_skipped += 1
                            continue

                        # --- Step 1: ensure Formula exists if this is a calculated column ---
                        formula = None
                        if meta.get("formula_key"):
                            f_key = meta["formula_key"]
                            f_meta = FORMULAS_REGISTRY.get(f_key)

                            if not f_meta:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"❌ Formula definition missing in registry for key '{f_key}'"
                                    )
                                )
                            else:
                                formula_defaults = {
                                    "title": f_meta["title"],
                                    "description": f_meta.get("description", ""),
                                    "expression": f_meta["expression"],
                                    "dependencies": f_meta.get("dependencies", []),
                                    "decimal_places": f_meta.get("decimal_places", 2),
                                    "is_system": f_meta.get("is_system", True),
                                }
                                formula, f_created = Formula.objects.update_or_create(
                                    key=f_key,
                                    defaults=formula_defaults,
                                )
                                if f_created:
                                    formula_created += 1
                                    self.stdout.write(self.style.SUCCESS(
                                        f"🆕 Created Formula: {f_key}"))
                                else:
                                    formula_updated += 1
                                    self.stdout.write(self.style.SUCCESS(
                                        f"🔄 Updated Formula: {f_key}"))

                        # --- Step 2: create/update SchemaColumnTemplate ---
                        defaults = {
                            "schema_type": schema_type,
                            "title": meta["title"],
                            "data_type": meta["data_type"],
                            "field_path": meta.get("field_path"),
                            "is_editable": meta.get("is_editable", True),
                            "is_default": meta.get("is_default", True),
                            "is_deletable": meta.get("is_deletable", True),
                            "is_system": meta.get("is_system", True),
                            "constraints": convert_decimal(meta.get("constraints", {})),
                            "display_order": meta.get("display_order", 0),
                            "formula": formula,
                            "source": source,
                        }

                        obj, created_flag = SchemaColumnTemplate.objects.update_or_create(
                            account_model_ct=account_model_ct,
                            schema_type=schema_type,
                            source=source,
                            source_field=source_field,
                            defaults=defaults,
                        )

                        if created_flag:
                            template_created += 1
                            self.stdout.write(self.style.SUCCESS(
                                f"🆕 Created Template: {obj.title}"))
                        else:
                            template_updated += 1
                            self.stdout.write(self.style.SUCCESS(
                                f"🔄 Updated Template: {obj.title}"))

        # --- Final summary ---
        self.stdout.write(self.style.SUCCESS(
            f"✅ Templates -> Created: {template_created}, Updated: {template_updated}, Skipped: {template_skipped}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"✅ Formulas  -> Created: {formula_created}, Updated: {formula_updated}"
        ))
