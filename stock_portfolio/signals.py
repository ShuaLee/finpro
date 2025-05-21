from django.db.models.signals import post_save
from django.dispatch import receiver
from portfolio.models import Portfolio
from .models import StockPortfolio, StockPortfolioSchema

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
            'name': 'Ticker',
            'data_type': 'string',
            'source': 'asset',
            'source_field': 'ticker',
            'editable': False
        },
        {
            'name': 'Quantity',
            'data_type': 'decimal',
            'source': 'holding',
            'source_field': 'quantity',
            'editable': True
        },
        {
            'name': 'Value',
            'data_type': 'decimal',
            'source': 'calculated',
            'source_field': 'current_value',
            'editable': False
        },
        {
            'name': 'Performance',
            'data_type': 'decimal',
            'source': 'calculated',
            'source_field': 'performance',
            'editable': False
        }
    ]


"""
@receiver(post_save, sender=StockPortfolio)
def create_default_schema(sender, instance, created, **kwargs):
    if created:
        schema = Schema.objects.create(
            portfolio=instance.portfolio, name='Default Schema')
        SchemaColumn.objects.create(
            schema=schema,
            name='Ticker',
            data_type='string',
            source='asset',
            source_field='ticker'
        )
        SchemaColumn.objects.create(
            schema=schema,
            name='Shares Owned',
            data_type='decimal',
            source='holding',
            source_field='shares'
        )
        SchemaColumn.objects.create(
            schema=schema,
            name='Last Price',
            data_type='decimal',
            source='asset',
            source_field='last_price'
        )
        instance.default_self_managed_schema = schema
        instance.save()
        logger.debug(
            f"Created default schema for StockPortfolio {instance.id}")
"""
