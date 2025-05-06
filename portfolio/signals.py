from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Portfolio
from core.models import Profile
from stock_portfolio.constants import SKELETON_SCHEMA
from stock_portfolio.models import StockPortfolio, Schema, SchemaColumn


@receiver(post_save, sender=Profile)
def create_individual_portfolio(sender, instance, created, **kwargs):
    if not created:
        return

    portfolio = Portfolio.objects.create(profile=instance)

    stock_portfolio = StockPortfolio(portfolio=portfolio)

    stock_portfolio.save()

