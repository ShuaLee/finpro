from django.db.models.signals import post_save
from django.dispatch import receiver
from portfolio.models import Portfolio
from .models import StockPortfolio, StockPortfolioSchema, SchemaColumn


@receiver(post_save, sender=Portfolio)
def create_stock_portfolio(sender, instance, created, **kwargs):
    if created:
        stock_portfolio = StockPortfolio.objects.create(portfolio=instance)
        # stock_portfolio.save()  # Explicitly call save to trigger initialize_default_schema

@receiver(post_save, sender=StockPortfolio)
def create_default_schema(sender, instance, created, **kwargs):
    """
    As soon as a StockPortfolio is created, add a StockPortfolioSchema
    named 'Default' so that every new portfolio starts with one.
    """
    if created:
        StockPortfolioSchema.objects.create(
            stock_portfolio=instance,
            name="Default",
        )

@receiver(post_save, sender=StockPortfolioSchema)
def ensure_default_columns(sender, instance, created, **kwargs):
    if created:
        # Ensure that default columns are created
        default_columns = [
            {"title": "Ticker", "source": "stock.ticker", "editable": False, "is_deletable": False, "column_type": "stock"},
            {"title": "Company Name", "source": "stock.long_name", "editable": True, "is_deletable": True, "column_type": "stock"},
            {"title": "Shares", "source": "holding.shares", "editable": True, "is_deletable": True, "column_type": "holding"},
            {"title": "Price", "source": "stock.price", "editable": True, "is_deletable": True, "column_type": "stock"},
            {"title": "Total Value", "source": "calculated.total_value", "editable": False, "is_deletable": True, "column_type": "calculated"},
        ]

        for col in default_columns:
            value_type = get_value_type_from_source(col["source"])
            SchemaColumn.objects.create(
                schema=instance,
                title=col["title"],
                source=col["source"],
                editable=col["editable"],
                is_deletable=col["is_deletable"],
                column_type=col["column_type"],
                value_type=value_type
            )

def get_value_type_from_source(source):

    return SchemaColumn.SOURCE_VALUE_TYPE_MAP.get(source, "text")  # Default to 'text' if not mapped