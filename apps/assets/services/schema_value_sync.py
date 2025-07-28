from django.apps import apps
from django.db import transaction
from assets.config import get_asset_schema_config
from schemas.models import SchemaColumn, SchemaColumnValue


class HoldingSchemaEngine:
    def __init__(self, holding, asset_type: str):
        self.holding = holding
        self.asset_type = asset_type
        self.portfolio = self._get_portfolio()
        self.schema = self._get_active_schema()
        self.config = get_asset_schema_config(asset_type)

    def _get_portfolio(self):
        # assumes account > subportfolio > portfolio
        return self.holding.account.sub_portfolio

    def _get_active_schema(self):
        SchemaModel = apps.get_model("schemas", "Schema")
        return SchemaModel.objects.filter(
            content_type__model=self.asset_type,
            object_id=self.portfolio.pk
        ).first()

    def resolve_value(self, field_path: str):
        parts = field_path.split('.')
        value = self.holding
        for part in parts:
            value = getattr(value, part, None)
            if value is None:
                return None
        return value

    def get_configured_value(self, column: SchemaColumn):
        column_title = column.title
        column_config = self.config.get(column_title)
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
            return

        for column in self.schema.columns.all():
            value = self.get_configured_value(column)
            if value is None:
                continue

            scv, created = SchemaColumnValue.objects.update_or_create(
                holding=self.holding,
                column=column,
                defaults={"value": value}
            )
