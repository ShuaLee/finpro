from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from portfolios.config import SUBPORTFOLIO_CONFIG
from portfolios.models.portfolio import Portfolio
from portfolios.models.subportfolio import SubPortfolio
from accounts.config.account_model_registry import get_account_model_map
from schemas.models import Schema
from schemas.services.schema_generator import SchemaGenerator


class SubPortfolioManager:
    """
    Service class for handling lifecycle and business logic of sub-portfolios
    (stocks, crypto, metals, custom, etc.).
    """

    @staticmethod
    def create_subportfolio(
        portfolio: Portfolio,
        type: str,
        name: str = None,
        slug: str = None,
        schema_name_fn=None,
    ) -> SubPortfolio:
        """
        Creates a SubPortfolio for the given Portfolio.

        Args:
            portfolio (Portfolio): The main portfolio.
            type (str): Subportfolio type (stock, crypto, metal, custom).
            name (str, optional): For custom subportfolios.
            slug (str, optional): For custom subportfolios.
            schema_namer_fn (callable, optional): Custom schema name formatter.

        Returns:
            SubPortfolio
        """
        if type not in SUBPORTFOLIO_CONFIG:
            raise ValidationError(f"Unknown subportfolio type: {type}")

        cfg = SUBPORTFOLIO_CONFIG[type]

        with transaction.atomic():
            # 1. Uniqueness check
            if cfg["unique"]:
                if SubPortfolio.objects.filter(portfolio=portfolio, type=type).exists():
                    raise ValidationError(
                        f"{type.capitalize()} portfolio already exists for this portfolio."
                    )

            # 2. Create SubPortfolio row
            subportfolio = SubPortfolio.objects.create(
                portfolio=portfolio, type=type, name=name, slug=slug
            )

            # 3. Get account models for this type (from registry)
            account_model_map = get_account_model_map(cfg["schema_type"])

            # 4. Generate schema(s) via SchemaGenerator
            generator = SchemaGenerator(subportfolio, cfg["schema_type"])
            generator.initialize(
                account_model_map=account_model_map,
                custom_schema_namer=schema_name_fn,
            )

            return subportfolio

    @staticmethod
    def delete_subportfolio(subportfolio: SubPortfolio):
        """
        Deletes a SubPortfolio and its associated schema.
        """
        ct = ContentType.objects.get_for_model(SubPortfolio)
        Schema.objects.filter(
            content_type=ct, object_id=subportfolio.id).delete()
        subportfolio.delete()
