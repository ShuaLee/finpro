from django.db import transaction
from django.core.exceptions import ValidationError
from portfolios.models.portfolio import Portfolio
from portfolios.models.stock import StockPortfolio
from schemas.services.schema import initialize_stock_schema


@transaction.atomic
def create_stock_portfolio(portfolio: Portfolio) -> StockPortfolio:
    """
    Creates a StockPortfolio for the given Portfolio and initializes its default schema.
    """
    # Check if the stock portfolio already exists
    if hasattr(portfolio, "stockportfolio"):
        raise ValidationError(
            "StockPortfolio already exists for this portfolio.")

    # Create the stock portfolio
    stock_portfolio = StockPortfolio.objects.create(portfolio=portfolio)

    # ✅ Create the default schema and columns for this stock portfolio
    initialize_stock_schema(stock_portfolio)

    return stock_portfolio
