from django.db.models.signals import post_save
from django.dispatch import receiver
from portfolio.models import Portfolio
from .models import StockPortfolio, StockPortfolioSchema, StockPortfolioSchemaColumn
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
        },
    ]

    # Create default columns
    for column_data in default_columns:
        StockPortfolioSchemaColumn.objects.create(
            schema=schema,
            **column_data
        )
