from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from portfolio.models import Portfolio
from .constants import DEFAULT_STOCK_SCHEMA_COLUMNS
from .models import StockPortfolio, StockPortfolioSchema, StockPortfolioSchemaColumn, StockPortfolioSchemaColumnValue, StockHolding
import logging
import threading

_thread_local = threading.local()

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
    for column_data in DEFAULT_STOCK_SCHEMA_COLUMNS:
        StockPortfolioSchemaColumn.objects.create(schema=schema, **column_data)


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


"""
Account values
"""

"""
@receiver([post_save, post_delete], sender=StockHolding)
def update_account_current_value_fx(sender, instance, **kwargs):
    account = instance.self_managed_account
    account.current_value_fx = account.get_total_current_value_in_profile_fx()
    account.save(update_fields=['current_value_fx'])
"""

"""
@receiver(post_save, sender=StockPortfolioSchemaColumnValue)
def update_account_on_column_value_change(sender, instance, **kwargs):
    if getattr(_thread_local, 'skip_column_value_signal', False):
        return

    account = instance.holding.self_managed_account
    account.current_value_fx = account.get_total_current_value_in_profile_fx()
    account.save(update_fields=['current_value_fx'])
"""
