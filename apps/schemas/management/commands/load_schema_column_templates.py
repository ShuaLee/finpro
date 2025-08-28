from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from formulas.models import Formula

from schemas.models import SchemaColumnTemplate
from schemas.config import SCHEMA_CONFIG_REGISTRY
from schemas.config.schema_registry.utils import validate_constraints

from decimal import Decimal


def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(v) for v in obj]
    return obj


class Command(BaseCommand):
    help = "Load schema column templates from SCHEMA_CONFIG_REGISTRY into the DB"

    def handle(self, *args, **kwargs):
        created, updated, skipped = 0, 0, 0

        for schema_type, variant_map in SCHEMA_CONFIG_REGISTRY.items():
            for account_model, fields in variant_map.items():
                account_model_ct = ContentType.objects.get_for_model(
                    account_model)

                for source, columns in fields.items():
                    for source_field, meta in columns.items():
                        try:
                            validate_constraints(
                                meta["data_type"],
                                convert_decimal(meta.get("constraints", {}))
                            )
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f"Constraint validation failed for {source_field}: {e}"
                            ))
                            skipped += 1
                            continue

                        defaults = {
                            "schema_type": schema_type,
                            "title": meta["title"],
                            "data_type": meta["data_type"],
                            "field_path": meta.get("field_path"),
                            "is_editable": meta.get("is_editable", True),
                            "is_default": meta.get("is_default", True),
                            "is_deletable": meta.get("is_deletable", True),
                            "is_system": meta.get("is_system", True),
                            "formula_method": meta.get("formula_method"),
                            "formula_expression": meta.get("formula_expression"),
                            "constraints": convert_decimal(meta.get("constraints", {})),
                            "display_order": meta.get("display_order", 0),
                            "investment_theme_id": meta.get("investment_theme_id"),
                        }

                        obj, created_flag = SchemaColumnTemplate.objects.update_or_create(
                            account_model_ct=account_model_ct,
                            source=source,
                            source_field=source_field,
                            defaults=defaults
                        )

                        if created_flag:
                            created += 1
                        else:
                            updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Created: {created}, Updated: {updated}, Skipped: {skipped}"))
