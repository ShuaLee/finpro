from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from assets.services.config import get_asset_schema_config
from schemas.models import SchemaColumn, SchemaColumnValue
from asteval import Interpreter
from decimal import Decimal


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

    def sync_column(self, column):
        if not column.source_field and not column.formula and not column.formula_expression:
            print(f"⚠️ Column {column.title} has no valid source or formula. Skipping.")
            return

        value = self.get_configured_value(column)
        if value is None:
            print(f"⚠️ Skipping column {column.title}, could not resolve value.")
            return

        content_type = ContentType.objects.get_for_model(self.holding)

        value_obj, created = SchemaColumnValue.objects.get_or_create(
            column=column,
            account_ct=content_type,
            account_id=self.holding.id,
            defaults={"value": value}
        )

        if not created and not value_obj.is_edited:
            value_obj.value = value
            value_obj.save()

        print(f"✅ Column synced: {column.title} = {value}")

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

    def get_all_available_values(self):
        """
        Collect all values from known config sources.
        """
        values = {}

        for source in ["asset", "holding"]:
            config_group = self.config.get(source, {})
            for field, meta in config_group.items():
                val = self.resolve_value(meta.get("field_path"))
                try:
                    values[field] = Decimal(str(val)) if val is not None else None
                except:
                    values[field] = val

        return values

    def evaluate_expression(self, expression: str):
        """
        Evaluates a safe math expression using resolved variables.
        """
        variables = self.get_all_available_values()
        aeval = Interpreter()

        for key, val in variables.items():
            aeval.symtable[key] = val

        try:
            result = aeval(expression)
            print(f"🧮 Evaluated '{expression}' -> {result}")
            return result
        except Exception as e:
            print(f"❌ Formula eval failed: {expression} -> {e}")
            return None

    def get_configured_value(self, column: SchemaColumn):
        if column.source != "calculated":
            config = self.get_column_config_by_field(column.source, column.source_field)

            # Fallback if config not found, try direct path from source + source_field
            if not config:
                if column.source_field:
                    return self.resolve_value(f"{column.source}.{column.source_field}")
                return None

            return self.resolve_value(config.get("field_path"))

        # Priority 1: User-defined formula
        if column.formula_expression:
            return self.evaluate_expression(column.formula_expression)

        # Priority 2: Backend formula
        if column.formula:
            return self.evaluate_expression(column.formula)

        return None

    @transaction.atomic
    def sync_all_columns(self):
        if not self.schema:
            print("🚫 No schema set on engine. Exiting sync.")
            return

        print(f"🔁 Syncing columns for holding {self.holding} with schema {self.schema}")
        for column in self.schema.columns.all():
            self.sync_column(column)
