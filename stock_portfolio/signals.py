from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from portfolio.models import Portfolio
from .models import StockPortfolio, StockPortfolioSchema, StockPortfolioSchemaColumn, StockPortfolioSchemaColumnValue, StockHolding
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Portfolio)
def create_stock_portfolio(sender, instance, created, **kwargs):
    if not created:
        return

    # Create StockPortfolio
    stock_portfolio = StockPortfolio.objects.create(portfolio=instance)

    # Create StockPortfolioSchema
    schema = StockPortfolioSchema.objects.create(
        stock_portfolio=stock_portfolio,
        name=f"Default Schema for {stock_portfolio}"
    )

    # Define default columns (adjust as needed)
    default_columns = [
        {
            'title': 'Ticker',
            'data_type': 'string',
            'source': 'asset',
            'source_field': 'ticker',
            'editable': False,
            'is_deletable': False,
        },
        {
            'title': 'Quantity',
            'data_type': 'decimal',
            'source': 'holding',
            'source_field': 'quantity',
            'editable': True,
            'is_deletable': False,
        },
        {
            'title': 'Price',
            'data_type': 'decimal',
            'source': 'asset',
            'source_field': 'price',
            'editable': True,
            'is_deletable': False,
        },
        {
            'title': 'Value',
            'data_type': 'decimal',
            'source': 'calculated',
            'source_field': 'current_value',
            'editable': False,
            'is_deletable': False,
            'formula': 'quantity * price'
        },
    ]

    # Create default columns
    for column_data in default_columns:
        StockPortfolioSchemaColumn.objects.create(
            schema=schema,
            **column_data
        )


@receiver(post_save, sender=StockHolding)
def create_column_values(sender, instance, created, **kwargs):
    if created:
        account = instance.self_managed_account
        schema = account.active_schema
        if not schema:
            logger.warning(
                f"No active schema for SelfManagedAccount {account.id}")
            return
        for column in schema.columns.all():
            StockPortfolioSchemaColumnValue.objects.create(
                column=column,
                holding=instance,
                value=None,
                is_edited=False
            )
        logger.info(
            f"Created column values for StockHolding {instance.id} in schema {schema.id}")


@receiver(post_delete, sender=StockHolding)
def delete_column_values(sender, instance, **kwargs):
    instance.column_values.all().delete()
    logger.info(f"Deleted column values for StockHolding {instance.id}")
