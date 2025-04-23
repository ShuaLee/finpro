from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Stock


@receiver(post_save, sender=Stock)
def fetch_stock_data(sender, instance, created, **kwargs):
    if created:  # Only run when the stock is first created
        instance.fetch_yfinance_data(force_update=True)