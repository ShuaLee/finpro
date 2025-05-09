from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SchemaColumn, SchemaColumnValue
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SchemaColumn)
def create_values_on_column_create(sender, instance, created, **kwargs):
    if created:
        try:
            portfolio = instance.schema.portfolio
            # Get the app label and holding model dynamically
            app_label = portfolio._meta.app_label  # e.g., 'stock_portfolio'
            holding_model_name = 'StockHolding' if app_label == 'stock_portfolio' else 'CryptoHolding'
            holding_model = apps.get_model(app_label, holding_model_name)
            accounts = portfolio.accounts.all()  # Assuming accounts related_name
            if not accounts.exists():
                logger.debug(
                    f"No accounts for portfolio {portfolio.id}, skipping SchemaColumnValue generation")
                return
            holdings = holding_model.objects.filter(stock_account__in=accounts)
            if not holdings.exists():
                logger.debug(
                    f"No holdings for portfolio {portfolio.id}, skipping SchemaColumnValue generation")
                return
            for holding in holdings:
                value = None
                if instance.source == 'asset' and instance.source_field:
                    value = str(
                        getattr(holding.asset, instance.source_field, None))
                elif instance.source == 'holding' and instance.source_field:
                    value = str(getattr(holding, instance.source_field, None))
                SchemaColumnValue.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(holding),
                    object_id=holding.id,
                    column=instance,
                    defaults={'value': value, 'is_edited': False}
                )
            logger.debug(
                f"Generated SchemaColumnValues for column {instance.name}")
        except Exception as e:
            logger.error(f"Error generating SchemaColumnValues: {str(e)}")
            raise
