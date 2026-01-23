from django.core.management.base import BaseCommand
from schemas.models.schema import Schema
from schemas.services.schema_manager import SchemaManager


class Command(BaseCommand):
    help = "Resequence all SchemaColumns in every Schema so display_order is continuous."

    def handle(self, *args, **options):
        total_fixed = 0

        for schema in Schema.objects.all():
            manager = SchemaManager(schema)
            before = list(schema.columns.order_by("display_order")
                          .values_list("id", "display_order"))

            manager.resequence_for_schema(schema)

            after = list(schema.columns.order_by("display_order")
                         .values_list("id", "display_order"))

            if before != after:
                total_fixed += 1
                self.stdout.write(
                    f"✅ Resequenced schema {schema.id} ({schema.account_type}) "
                    f"for portfolio {schema.portfolio_id}"
                )

        self.stdout.write(
            self.style.SUCCESS(f"🎯 Done. Resequenced {total_fixed} schema(s).")
        )
