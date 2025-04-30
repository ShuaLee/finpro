from django.db.models.signals import post_save
from django.dispatch import receiver
from .constants import PREDEFINED_COLUMNS
from .models import Stock, StockHolding, SchemaColumnValue, Schema
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


@receiver(post_save, sender=StockHolding)
def create_schema_column_values(sender, instance, created, **kwargs):
    if not created:
        return

    stock_portfolio = instance.stock_account.stock_portfolio
    schemas = stock_portfolio.schemas.all()

    for schema in schemas:
        for column in schema.columns.all():
            value = None

            # Fetch value from stock or holding if it's a predefined field
            if column.source in PREDEFINED_COLUMNS:
                # Use source_field instead of column.name to match predefined field
                predefined_field = None
                if column.source_field:
                    predefined_field = next(
                        (item['field'] for item in PREDEFINED_COLUMNS[column.source]
                         if item['field'] == column.source_field),
                        None
                    )

                if predefined_field:
                    source_object = instance.stock if column.source == 'stock' else instance
                    if hasattr(source_object, predefined_field):
                        value = getattr(source_object, predefined_field)
                        logger.debug(
                            f"Assigned value {value} for {column.source}.{predefined_field}")
                    else:
                        logger.warning(
                            f"Field {predefined_field} not found on {column.source} object")
                else:
                    logger.warning(
                        f"No matching predefined field for {column.source}.{column.source_field}")

            # Create or update SchemaColumnValue
            SchemaColumnValue.objects.get_or_create(
                stock_holding=instance,
                column=column,
                defaults={'value': str(value) if value is not None else None}
            )
