from django.core.management.base import BaseCommand
from schemas.models.template import SchemaTemplate, SchemaTemplateColumn
from schemas.config.schema_templates.equity_template import EQUITY_TEMPLATE_CONFIG


class Command(BaseCommand):
    help = "Seed the Equity SchemaTemplate and its default columns."

    def handle(self, *args, **kwargs):
        cfg = EQUITY_TEMPLATE_CONFIG

        template, created = SchemaTemplate.objects.update_or_create(
            account_type=cfg["account_type"],
            defaults={
                "name": cfg["name"],
                "description": cfg["description"],
                "is_active": True,
            },
        )

        for col in cfg["columns"]:
            obj, col_created = SchemaTemplateColumn.objects.update_or_create(
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
                    "display_order": col.get("display_order", None),
                },
            )
            self.stdout.write(
                f"{'Created' if col_created else 'Updated'}: {obj.title}")

        self.stdout.write(self.style.SUCCESS(
            "✅ Equity Schema Template seeded successfully."))
