from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from schemas.models import SchemaColumnTemplate
from schemas.config import SCHEMA_CONFIG_REGISTRY
from accounts.config.account_model_registry import ACCOUNT_MODEL_MAP
from schemas.config.utils import validate_constraints


class Command(BaseCommand):
    help = "Load schema column templates from SCHEMA_CONFIG_REGISTRY into the DB"

    def handle(self, *args, **kwargs):
        created, updated, skipped = 0, 0, 0

        for schema_type, variant_map in SCHEMA_CONFIG_REGISTRY.items():
            for variant_key, fields in variant_map.items():
                account_model = ACCOUNT_MODEL_MAP.get(schema_type, {}).get(variant_key)
                if not account_model:
                    self.stdout.write(self.style.WARNING(
                        f"No model registered for {schema_type} [{variant_key}]"
                    ))
                    continue

                account_model_ct = ContentType.objects.get_for_model(account_model)

                for source, columns in fields.items():
                    for source_field, meta in columns.items():
                        try:
                            validate_constraints(meta["data_type"], meta.get("constraints", {}))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f"Constraint validation failed for {source_field}: {e}"
                            ))
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
                            "constraints": meta.get("constraints", {}),
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

        self.stdout.write(self.style.SUCCESS(f"✅ Created: {created}, Updated: {updated}, Skipped: {skipped}"))
