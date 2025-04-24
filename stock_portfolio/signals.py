from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Stock
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
            logger.warning(f"Stock creation failed for {instance.ticker}: No data fetched.")
        
        instance.save()
