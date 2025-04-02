from django.db.models.signals import post_save
from django.dispatch import receiver
from portfolio.models import Portfolio
from .models import StockPortfolio


@receiver(post_save, sender=Portfolio)
def create_stock_portfolio(sender, instance, created, **kwargs):
    if created:
        stock_portfolio = StockPortfolio.objects.create(portfolio=instance)
        # stock_portfolio.save()  # Explicitly call save to trigger initialize_default_schema
