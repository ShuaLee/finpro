import logging

logger = logging.getLogger(__name__)

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
