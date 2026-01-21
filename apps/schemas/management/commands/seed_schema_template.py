from django.core.management.base import BaseCommand

from accounts.models import AccountType
from schemas.models.template import SchemaTemplate, SchemaTemplateColumn
from schemas.seed.registry import get_all_schema_templates


class Command(BaseCommand):
    help = "Seed system schema templates"

    def handle(self, *args, **kwargs):
        for config in get_all_schema_templates():
            slug = config["account_type_slug"]

            try:
                account_type = AccountType.objects.get(slug=slug)
            except AccountType.DoesNotExist:
                self.stderr.write(f"❌ AccountType not found: {slug}")
                continue

            template, _ = SchemaTemplate.objects.update_or_create(
                account_type=account_type,
                defaults={
                    "name": config["name"],
                    "description": config["description"],
                    "is_active": True,
                },
            )

            for col in config["columns"]:
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

            self.stdout.write(
                self.style.SUCCESS(f"✅ Seeded schema: {config['name']}")
            )
