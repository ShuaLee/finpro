from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from assets.services.config import get_asset_schema_config
from schemas.models import SchemaColumn, SchemaColumnValue


class HoldingSchemaEngine:
    def __init__(self, holding, asset_type: str):
        self.holding = holding
        self.asset_type = asset_type
        self.portfolio = self._get_portfolio()
        print(f"🧪 Engine Init: holding={holding.id}, portfolio={self.portfolio}")
        self.schema = self._get_active_schema()
        self.config = get_asset_schema_config(asset_type)
        print(f"🧪 Schema found: {self.schema}")

    def _get_portfolio(self):
        # assumes account > subportfolio > portfolio
        return self.holding.account.sub_portfolio

    def _get_active_schema(self):
        SchemaModel = apps.get_model("schemas", "Schema")
        return SchemaModel.objects.filter(
            content_type=ContentType.objects.get_for_model(self.portfolio),
            object_id=self.portfolio.pk
        ).first()

    def resolve_value(self, field_path: str):
        print(f"🔍 Resolving path: {field_path}")
        parts = field_path.split('.')
        value = self.holding
        for part in parts:
            print(f"  👉 getattr({value}, '{part}')")
            value = getattr(value, part, None)
            if value is None:
                print(f"  ❌ Failed at: {part}")
                return None
        print(f"✅ Resolved value: {value}")
        return value
    
    def get_column_config_by_field(self, source: str, field: str):
        return self.config.get(source, {}).get(field)

    def get_configured_value(self, column: SchemaColumn):
        column_config = self.get_column_config_by_field(column.source, column.source_field)
        print(f"🔍 COLUMN={column.title} | source={column.source} | field={column.source_field} | config={column_config}")

        if not column_config:
            return None

        if "field_path" in column_config:
            return self.resolve_value(column_config["field_path"])

        elif "formula_method" in column_config:
            method_name = column_config["formula_method"]
            if hasattr(self.holding, method_name):
                return getattr(self.holding, method_name)()
        return None

    @transaction.atomic
    def sync_all_columns(self):
        if not self.schema:
            print("🚫 No schema set on engine. Exiting sync.")
            return

        content_type = ContentType.objects.get_for_model(self.holding.__class__)
        print(f"🔁 Syncing columns for holding {self.holding} with schema {self.schema}")

        for column in self.schema.columns.all():
            print(f"🔍 Processing column: {column.title} ({column.source}.{column.source_field})")
            value = self.get_configured_value(column)
            print(f"➡️ Value resolved: {value}")

            if value is None:
                print(f"⚠️ Skipping column {column.title}, value could not be resolved.")
                continue

            SchemaColumnValue.objects.update_or_create(
                column=column,
                account_ct=content_type,
                account_id=self.holding.id,
                defaults={"value": value}
            )
            print(f"✅ Column synced: {column.title} = {value}")
