from django.core.management.base import BaseCommand
from schemas.models.template import SchemaTemplate, SchemaTemplateColumn


TEMPLATES = [
    {
        "account_type_slug": "brokerage",
        "name": "Equity Schema Template",
        "description": "Default schema template for equity portfolios.",
        "columns": [  # ... copy from EQUITY_TEMPLATE_CONFIG['columns']
            # (paste them here as-is)
        ],
    },
    {
        "account_type_slug": "crypto_wallet",
        "name": "Crypto Schema Template",
        "description": "Default schema template for crypto portfolios.",
        "columns": [  # ... copy from CRYPTO_TEMPLATE_CONFIG['columns']
            # (paste them here as-is)
        ],
    },
]


class Command(BaseCommand):
    help = "Seed schema templates (equity, crypto) and their default columns."

    def handle(self, *args, **kwargs):
        for template_cfg in TEMPLATES:
            account_type = template_cfg["account_type_slug"]
            template, _ = SchemaTemplate.objects.update_or_create(
                account_type=account_type,
                defaults={
                    "name": template_cfg["name"],
                    "description": template_cfg["description"],
                    "is_active": True,
                },
            )

            for col in template_cfg["columns"]:
                obj, created = SchemaTemplateColumn.objects.update_or_create(
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
                        "constraints": col.get("constraints", {}),
                    },
                )
                self.stdout.write(f"{'Created' if created else 'Updated'}: {obj.title}")

        self.stdout.write(self.style.SUCCESS("✅ Schema templates seeded."))
