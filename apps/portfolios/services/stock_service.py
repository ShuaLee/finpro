from django.db import transaction
from django.core.exceptions import ValidationError
from portfolios.models.portfolio import Portfolio
from portfolios.models.stock import StockPortfolio
from schemas.services.schema_initialization import initialize_stock_schema

def create_asset_portfolio(portfolio: Portfolio, portfolio_model_class, schema_initializer_fn, related_name: str):
    """
    Generic creator for any asset portfolio (stocks, crypto, etc.).
    Ensures uniqueness and initializes schema.
    
    Args:
        portfolio (Portfolio): The user's main portfolio.
        portfolio_model_class (Model): The subportfolio model to create (e.g., CryptoPortfolio).
        schema_initializer_fn (Callable): A function that initializes the default schema.
        related_name (str): The related_name used on Portfolio (e.g., 'stockportfolio').
    
    Returns:
        The created subportfolio instance.
    """
    with transaction.atomic():
        # Check if the subportfolio already exists
        if hasattr(portfolio, related_name):
            raise ValidationError(
                f"{portfolio_model_class.__name__} already exists for this portfolio."
            )
        
        # Create the subportfolio
        subportfolio = portfolio_model_class.objects.create(portfolio=portfolio)

        # Initialize the default schema
        schema_initializer_fn(subportfolio)

        return subportfolio



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
