from django.core.exceptions import ValidationError
from portfolios.models.portfolio import Portfolio
from portfolios.models.stock import StockPortfolio


def create_stock_portfolio(portfolio: Portfolio) -> StockPortfolio:
    """
    Creates a StockPortfolio for the given Portfolio.

    Raises:
        ValidationError if StockPortfolio already exists.
    """
    if hasattr(portfolio, "stockportfolio"):
        raise ValidationError(
            "StockPortfolio already exists for this portfolio.")

    return StockPortfolio.objects.create(portfolio=portfolio)


def initialize_stock_schema(stock_portfolio: StockPortfolio):
    """
    Stub for schema initialization (future feature).
    """
    # Currently not implemented. Leave empty or log.
    pass

# """
# Stock Portfolio Service
# -----------------------

# This module provides services for managing StockPortfolio creation and initialization logic.
# It also handles schema setup (if required by business rules).
# """

# from django.db import transaction
# from django.core.exceptions import ValidationError
# from portfolios.models.portfolio import Portfolio
# from portfolios.models.stock import StockPortfolio
# from schemas.constants import DEFAULT_STOCK_SCHEMA_COLUMNS
# from schemas.models.stocks import StockPortfolioSchema, StockPortfolioSC


# def create_stock_portfolio(portfolio: Portfolio) -> StockPortfolio:
#     """
#     Creates a StockPortfolio for the given Portfolio.

#     Args:
#         portfolio (Portfolio): The main portfolio.

#     Returns:
#         StockPortfolio: The created StockPortfolio instance.

#     Raises:
#         ValidationError: If the portfolio already has a StockPortfolio.
#     """
#     if hasattr(portfolio, "stock_portfolio"):
#         raise ValidationError(
#             "StockPortfolio already exists for this portfolio.")

#     # Only one DB write → transaction.atomic() is unnecessary here
#     stock_portfolio = StockPortfolio.objects.create(portfolio=portfolio)
#     return stock_portfolio


# def initialize_stock_schema(stock_portfolio: StockPortfolio) -> None:
#     """
#     Creates a default schema and columns for the StockPortfolio.

#     Args:
#         stock_portfolio (StockPortfolio): The stock portfolio instance.
#     """
#     with transaction.atomic():
#         schema = StockPortfolioSchema.objects.create(
#             stock_portfolio=stock_portfolio,
#             name=f"Default Schema for {stock_portfolio}"
#         )

#         for column_data in DEFAULT_STOCK_SCHEMA_COLUMNS:
#             StockPortfolioSC.objects.create(schema=schema, **column_data)
