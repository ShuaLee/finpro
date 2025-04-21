from django.db.models.signals import post_save
from django.dispatch import receiver
from portfolio.models import Portfolio
from .models import StockPortfolio, StockPortfolioSchema, SchemaColumn


@receiver(post_save, sender=Portfolio)
def create_stock_portfolio(sender, instance, created, **kwargs):
    if created:
        stock_portfolio = StockPortfolio.objects.create(portfolio=instance)
        # stock_portfolio.save()  # Explicitly call save to trigger initialize_default_schema


@receiver(post_save, sender=StockPortfolioSchema)
def ensure_ticker_column(sender, instance, created, **kwargs):
    if created:
        # Only create "Ticker" column if it doesn't already exist (redundant but safe)
        if not instance.columns.filter(title="Ticker").exists():
            SchemaColumn.objects.create(
                schema=instance,
                title="Ticker",
                source="stock.ticker",
                editable=False,
                value_type="text",
                is_deletable=False
            )
