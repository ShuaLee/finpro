from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from portfolios.models.portfolio import Portfolio
from portfolios.models.subportfolio import SubPortfolio
from schemas.models import Schema
from schemas.services.schema_generator import SchemaGenerator
from core.types import DOMAIN_TYPE_REGISTRY


class SubPortfolioManager:
    """
    Service class for handling lifecycle and business logic of sub-portfolios
    (stock, crypto, metal, custom, etc.).
    """

    @staticmethod
    def create_subportfolio(
        portfolio: Portfolio,
        domain_type: str,
        name: str = None,
        slug: str = None,
        schema_name_fn=None,
    ) -> SubPortfolio:
        """
        Creates a SubPortfolio for the given Portfolio.

        Args:
            portfolio (Portfolio): The main portfolio.
            domain_type (str): One of DomainType (stock, crypto, metal, custom).
            name (str, optional): Custom name (mainly for custom type).
            slug (str, optional): Slug (mainly for custom type).
            schema_name_fn (callable, optional): Custom schema name formatter.

        Returns:
            SubPortfolio
        """
        if domain_type not in DOMAIN_TYPE_REGISTRY:
            raise ValidationError(f"Unknown subportfolio type: {domain_type}")

        cfg = DOMAIN_TYPE_REGISTRY[domain_type]

        with transaction.atomic():
            # 🚦 1. Uniqueness check (only one stock/crypto/metal per portfolio)
            if cfg.get("unique_subportfolio", False):
                if SubPortfolio.objects.filter(
                    portfolio=portfolio, type=domain_type
                ).exists():
                    raise ValidationError(
                        f"{cfg['default_subportfolio_name']} already exists for this portfolio."
                    )

            # 🆕 2. Auto-generate name/slug if not provided
            final_name = name or cfg.get(
                "default_subportfolio_name", f"{domain_type.capitalize()} Portfolio"
            )
            final_slug = slug or slugify(final_name)

            # 3. Create SubPortfolio row
            subportfolio = SubPortfolio.objects.create(
                portfolio=portfolio, type=domain_type, name=final_name, slug=final_slug
            )

            # 🛠 4. Generate schema for this subportfolio
            generator = SchemaGenerator(subportfolio, domain_type)
            generator.initialize(
                account_types=[domain_type],  # ✅ now just domain types
                custom_schema_namer=schema_name_fn,
            )

            return subportfolio

    @staticmethod
    def delete_subportfolio(subportfolio: SubPortfolio):
        """
        Deletes a SubPortfolio and its associated schema.
        """
        Schema.objects.filter(subportfolio=subportfolio).delete()
        subportfolio.delete()
