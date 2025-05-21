from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Portfolio
from core.models import Profile
from stock_portfolio.models import StockPortfolio


@receiver(post_save, sender=Profile)
def create_individual_portfolio(sender, instance, created, **kwargs):
    if not created:
        return

    # Create Portfolio
    portfolio = Portfolio.objects.create(profile=instance)

