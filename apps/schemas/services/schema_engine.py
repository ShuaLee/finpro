from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from schemas.models import SchemaColumn, SchemaColumnValue
from schemas.services.expression_evaluator import evaluate_expression
from decimal import Decimal, ROUND_DOWN
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
        # ✅ Column must have either a field_path (asset/holding/custom) or a formula (calculated)
        if not column.field_path and not column.formula:
            logger.debug(
                f"⚠️ Column {column.title} has no valid field_path or formula. Skipping."
            )
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
            raw_value = None
            if column.field_path:
                raw_value = self.resolve_value(column.field_path)
            elif column.source_field:
                raw_value = self.resolve_value(f"{column.source}.{column.source_field}")

            # --- Apply defaults if missing ---
            if raw_value is None:
                if column.data_type == "decimal":
                    dp = int(column.constraints.get("decimal_places", 2))
                    raw_value = Decimal("0").quantize(
                        Decimal(f"1.{'0'*dp}"),
                        rounding=ROUND_DOWN
                    )
                elif column.data_type == "string":
                    raw_value = "-"
            return raw_value

        # --- Calculated columns ---
        context = self.get_all_available_values()

        formula = column.effective_formula
        if formula and formula.expression and formula.expression.strip():
            try:
                return evaluate_expression(formula.expression, context)
            except Exception as e:
                logger.warning(
                    f"❌ Failed to evaluate formula '{formula.key}' "
                    f"for column '{column.title}': {e}"
                )
                # Default for calculated if it fails
                dp = int(column.constraints.get("decimal_places", 2))
                return Decimal("0").quantize(
                    Decimal(f"1.{'0'*dp}"),
                    rounding=ROUND_DOWN
                )

        # Default for calculated if no formula is present
        dp = int(column.constraints.get("decimal_places", 2))
        return Decimal("0").quantize(
            Decimal(f"1.{'0'*dp}"),
            rounding=ROUND_DOWN
        )


    @transaction.atomic
    def sync_all_columns(self):
        if not self.schema:
            logger.debug("🚫 No schema set on engine. Exiting sync.")
            return

        # ✅ Ensure missing SchemaColumnValues exist before syncing
        self.ensure_all_values_exist()

        cols = list(self.schema.columns.all())

        # 1) Sync base columns (asset/holding/custom)
        for c in cols:
            if c.source != "calculated":
                self.sync_column(c)

        # 2) Sync calculated columns
        for c in cols:
            if c.source == "calculated":
                self.sync_column(c)

    def ensure_all_values_exist(self):
        """
        Guarantee every SchemaColumn in the schema has a SchemaColumnValue
        for this holding. If missing, create with sensible defaults.
        """
        if not self.schema:
            return

        content_type = ContentType.objects.get_for_model(self.holding)

        for column in self.schema.columns.all():
            if SchemaColumnValue.objects.filter(
                column=column,
                account_ct=content_type,
                account_id=self.holding.id
            ).exists():
                continue  # already has a value

            # --- Default fallbacks ---
            default_val = None
            if column.data_type == "decimal":
                dp = int(column.constraints.get("decimal_places", 2))
                default_val = Decimal("0").quantize(
                    Decimal(f"1.{'0'*dp}"), rounding=ROUND_DOWN
                )
            elif column.data_type == "string":
                default_val = "-"
            else:
                default_val = None  # can extend later for dates, etc.

            # ✅ Always create missing SCV with default
            SchemaColumnValue.objects.create(
                column=column,
                account_ct=content_type,
                account_id=self.holding.id,
                value=default_val,
                is_edited=False,
            )
