from django.db.models.signals import post_save
from django.dispatch import receiver
from .constants import PREDEFINED_COLUMNS, SKELETON_SCHEMA
from .models import StockHolding, StockPortfolio, SchemaColumn, SchemaColumnValue, Schema, SelfManagedAccount
from .utils import evaluate_formula
import logging

logger = logging.getLogger(__name__)

# -------------------


def generate_schema_column_values_for_holding(holding):
    stock_portfolio = holding.stock_account.stock_portfolio
    schemas = stock_portfolio.schemas.prefetch_related('columns')

    for schema in schemas:
        for column in schema.columns.all():
            value = None

            # Handle predefined fields
            if column.source in PREDEFINED_COLUMNS:
                predefined_field = column.source_field
                if predefined_field:
                    source_object = holding.stock if column.source == 'stock' else holding
                    if hasattr(source_object, predefined_field):
                        value = getattr(source_object, predefined_field)
                    else:
                        logger.warning(
                            f"Field '{predefined_field}' not found on '{column.source}' object."
                        )
                else:
                    logger.warning(f"No source_field defined for {column}")

            # Handle calculated fields
            elif column.source == 'calculated' and column.source_field:
                value = evaluate_formula(column.source_field, holding)

            SchemaColumnValue.objects.get_or_create(
                stock_holding=holding,
                column=column,
                defaults={'value': str(value) if value is not None else None}
            )


def generate_schema_column_values_for_column(column):
    schema = column.schema
    holdings = StockHolding.objects.filter(
        stock_account__stock_portfolio=schema.stock_portfolio
    ).select_related('stock', 'stock_account')

    for holding in holdings:
        generate_schema_column_values_for_holding(holding)


@receiver(post_save, sender=StockHolding)
def create_column_values_on_holding_create(sender, instance, created, **kwargs):
    if created:
        generate_schema_column_values_for_holding(instance)


@receiver(post_save, sender=SchemaColumn)
def create_values_on_column_create(sender, instance, created, **kwargs):
    if created:
        generate_schema_column_values_for_column(instance)

# -------------------


@receiver(post_save, sender=StockPortfolio)
def create_default_schema(sender, instance, created, **kwargs):
    if not created:
        return

    schema = Schema.objects.create(
        stock_portfolio=instance,
        name=SKELETON_SCHEMA['name'],
    )

    for source, columns in SKELETON_SCHEMA['columns'].items():
        for column in columns:
            SchemaColumn.objects.create(
                schema=schema,
                name=column['label'],
                data_type=column['type'],
                source=source,
                source_field=column['field'],
            )

    instance.default_self_managed_schema = schema
    instance.save(update_fields=['default_self_managed_schema'])
