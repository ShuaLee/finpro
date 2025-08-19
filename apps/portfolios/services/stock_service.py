from django.db import transaction
from django.core.exceptions import ValidationError
from portfolios.models.portfolio import Portfolio
from accounts.config.account_model_registry import get_account_model_map
from schemas.services.schema_initialization import initialize_asset_schema

def create_asset_portfolio(
        portfolio: Portfolio, 
        portfolio_model_class, 
        related_name: str,
        schema_type: str,
        schema_namer_fn=None, 
        ):
    """
    Generic creator for any asset portfolio (stocks, crypto, etc.).
    Ensures uniqueness and initializes schema.

    Args:
        portfolio (Portfolio): The user's main portfolio.
        portfolio_model_class (Model): The subportfolio model to create (e.g., CryptoPortfolio).
        related_name (str): The related_name on Portfolio (e.g., 'stockportfolio').
        schema_type (str): Schema config name (e.g., 'stock', 'crypto').
        schema_namer_fn (callable, optional): Custom schema name formatter.
    """
    with transaction.atomic():
        # Check if the subportfolio already exists
        if hasattr(portfolio, related_name):
            raise ValidationError(
                f"{portfolio_model_class.__name__} already exists for this portfolio."
            )
        
        # Create the subportfolio
        subportfolio = portfolio_model_class.objects.create(portfolio=portfolio)

        # 🔁 Get account models for this asset type (from registry)
        account_model_map = get_account_model_map(schema_type)

        # ✅ Directly call the shared schema initializer here
        initialize_asset_schema(
            subportfolio=subportfolio,
            schema_type=schema_type,
            account_model_map=account_model_map,
            custom_schema_namer=schema_namer_fn,
        )

        return subportfolio
