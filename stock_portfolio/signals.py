from django.db.models.signals import post_save
from django.dispatch import receiver
from .constants import PREDEFINED_COLUMNS, SKELETON_SCHEMA
from .models import Stock, StockHolding, StockPortfolio, SchemaColumn, SchemaColumnValue, Schema, SelfManagedAccount
from .utils import evaluate_formula
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Stock)
def fetch_stock_data(sender, instance, created, **kwargs):
    if created:
        success = instance.fetch_yfinance_data(force_update=True)

        if success:
            instance.is_custom = not any([
                instance.short_name,
                instance.long_name,
                instance.exchange,
            ])
            logger.info(f"Stock {instance.ticker} fetched successfully.")
        else:
            instance.is_custom = True
            logger.warning(
                f"Stock creation failed for {instance.ticker}: No data fetched.")

        instance.save()


"""
Refractor
"""
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
        account__stock_portfolio=schema.stock_portfolio
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


"""
@receiver(post_save, sender=StockPortfolio)
def update_account_schemas_when_default_changes(sender, instance, created, **kwargs):
    if created:
        return  # It is alreay assigned at creation elsewhere

    # Update all accounts whose active_schema matches the old default or is null
    accounts = SelfManagedAccount.objects.filter(
        stock_portfolio=instance
    )

    for account in accounts:
        if account.active_schema != instance.default_schema:
            account.active_schema = instance.default_schema
            account.save(update_fields=['active_schema'])
"""
