from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Stock
import logging

logger = logging.getLogger(__name__)
""" 
@receiver(post_save, sender=Stock)
def fetch_stock_data(sender, instance, created, **kwargs):
    if created:
        # Disconnect signal to prevent recursion
        post_save.disconnect(fetch_stock_data, sender=Stock)
        try:
            success = instance.fetch_yfinance_data(force_update=True)
            # Set is_custom: True if fetch fails or key fields are missing
            instance.is_custom = not success or not any([
                instance.short_name,
                instance.long_name,
                instance.exchange,
            ])
            if success:
                logger.info(f"Stock {instance.ticker} fetched successfully.")
            else:
                logger.warning(f"Stock {instance.ticker}: No data fetched.")
            # Save only is_custom to avoid triggering other updates
            instance.save(update_fields=['is_custom'])
        finally:
            # Reconnect signal
            post_save.connect(fetch_stock_data, sender=Stock)
"""