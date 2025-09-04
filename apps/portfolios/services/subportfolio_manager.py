from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from portfolios.models.portfolio import Portfolio
from accounts.config.account_model_registry import get_account_model_map
from schemas.models import Schema
from schemas.services.schema_generator import SchemaGenerator

class SubPortfolioManager:
    """
    Service class for handling lifecycle and business logic of sub-portfolios
    (stocks, crypto, metals, custom, etc.).
    """

    @staticmethod
    def create_sub_portfolio(
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
            # 🚦 1. Ensure uniqueness
            if hasattr(portfolio, related_name):
                raise ValidationError(
                    f"{portfolio_model_class.__name__} already exists for this portfolio."
                )

            # 🆕 2. Create the subportfolio
            subportfolio = portfolio_model_class.objects.create(portfolio=portfolio)

            # 🔁 3. Get account models for this asset type (from registry)
            account_model_map = get_account_model_map(schema_type)

            # 🛠 4. Generate schema(s) via SchemaGenerator
            generator = SchemaGenerator(subportfolio, schema_type)
            generator.initialize(
                account_model_map=account_model_map,
                custom_schema_namer=schema_namer_fn,
            )

            return subportfolio
        
    @staticmethod
    def delete_subportfolio_with_schema(portfolio):
        """
        Deletes a subportfolio and its associated schema.
        """
        ct = ContentType.objects.get_for_model(portfolio.__class__)
        Schema.objects.filter(content_type=ct, object_id=portfolio.id).delete()
        portfolio.delete()
