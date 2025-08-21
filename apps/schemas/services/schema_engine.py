from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from schemas.models import SchemaColumn, SchemaColumnValue
from schemas.services.expression_evaluator import evaluate_expression
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class HoldingSchemaEngine:
    def __init__(self, holding, asset_type: str):
        self.holding = holding
        self.asset_type = asset_type
        self.portfolio = self._get_portfolio()

        logger.debug(
            f"🧪 Engine Init: holding={getattr(holding, 'id', holding)}, portfolio={self.portfolio}"
        )

        self.schema = self._get_active_schema()
        self.config = {}

        logger.debug(f"🧪 Schema found: {self.schema}")

    def _get_portfolio(self):
        # Self-managed holdings
        if hasattr(self.holding, "self_managed_account") and self.holding.self_managed_account:
            return self.holding.self_managed_account.stock_portfolio

        # Managed holdings (if/when you add them)
        if hasattr(self.holding, "managed_account") and self.holding.managed_account:
            return self.holding.managed_account.stock_portfolio

        raise AttributeError(
            "Holding does not link to a known account → sub-portfolio.")

    def _get_active_schema(self):
        try:
            SchemaModel = apps.get_model("schemas", "Schema")
        except LookupError:
            logger.exception(
                "❌ Unable to locate 'schemas.Schema' via apps registry")
            return None

        try:
            return SchemaModel.objects.filter(
                content_type=ContentType.objects.get_for_model(self.portfolio),
                object_id=self.portfolio.pk
            ).first()
        except Exception as e:
            logger.exception(f"❌ Failed to retrieve schema for portfolio: {e}")
            return None

    def sync_column(self, column):
        if not column.field_path and not column.formula_expression and not column.formula_method:
            logger.debug(
                f"⚠️ Column {column.title} has no valid field_path or formula. Skipping.")
            return

        value = self.get_configured_value(column)

        if value is None:
            logger.warning(
                f"⚠️ Skipping column '{column.title}' for holding {self.holding}. Could not resolve value."
            )
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

        logger.debug(f"✅ Column synced: {column.title} = {value}")

    def resolve_value(self, field_path: str):
        logger.debug(f"🔍 Resolving path: {field_path}")
        parts = field_path.split('.')
        value = self.holding
        for part in parts:
            logger.debug(f"  👉 getattr({value}, '{part}')")
            value = getattr(value, part, None)
            if value is None:
                logger.warning(
                    f"❌ Could not resolve value from field_path: {field_path}")
                return None
        logger.debug(f"✅ Resolved value: {value}")
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

                if isinstance(val, (int, float, str, Decimal)):
                    try:
                        values[field] = Decimal(
                            str(val)) if val is not None else None
                    except Exception:
                        logger.warning(
                            f"⚠️ Could not parse decimal for {field}: {val}")
                        values[field] = val
                else:
                    values[field] = val

        return values

    def get_configured_value(self, column: SchemaColumn):
        if column.source != "calculated":
            if column.field_path:
                return self.resolve_value(column.field_path)
            elif column.source_field:
                return self.resolve_value(f"{column.source}.{column.source_field}")
            return None

        context = self.get_all_available_values()

        if column.formula_expression and column.formula_expression.strip():
            return evaluate_expression(column.formula_expression, context)

        if column.formula_method:
            method = getattr(self.holding, column.formula_method, None)
            if method and callable(method):
                return method()

        return None

    @transaction.atomic
    def sync_all_columns(self):
        if not self.schema:
            logger.debug("🚫 No schema set on engine. Exiting sync.")
            return

        cols = list(self.schema.columns.all())

        # 1) Seed/update base columns (asset/holding/custom)
        for c in cols:
            if c.source != "calculated":
                self.sync_column(c)

        # 2) Compute calculated columns
        for c in cols:
            if c.source == "calculated":
                self.sync_column(c)
