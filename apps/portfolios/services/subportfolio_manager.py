from django.db import transaction, models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from portfolios.models.portfolio import Portfolio
from portfolios.models.subportfolio import SubPortfolio
from schemas.models import Schema
from schemas.services.schema_generator import SchemaGenerator
from accounts.services.detail_model_resolver import get_domain_meta_with_details


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
        print("🚀 SubPortfolioManager.create_subportfolio() CALLED")

        # ✅ Pull enriched metadata
        cfg = get_domain_meta_with_details(domain_type)

        with transaction.atomic():
            # 🚦 1. Uniqueness check
            if cfg.get("unique_subportfolio", False):
                if SubPortfolio.objects.filter(
                    portfolio=portfolio, type=domain_type
                ).exists():
                    raise ValidationError(
                        f"{cfg['default_subportfolio_name']} already exists for this portfolio."
                    )

            # 🆕 2. Auto-generate name/slug
            final_name = name or cfg.get(
                "default_subportfolio_name", f"{domain_type.capitalize()} Portfolio"
            )
            final_slug = slug or slugify(final_name)

            # 3. Create SubPortfolio row
            subportfolio = SubPortfolio.objects.create(
                portfolio=portfolio, type=domain_type, name=final_name, slug=final_slug
            )

            # 🛠 4. Generate schemas for all account types in this domain
            print("🔥 about to call generator.initialize()")
            generator = SchemaGenerator(subportfolio, domain_type)
            generator.initialize(custom_schema_namer=schema_name_fn)
            print("✅ finished generator.initialize()")

            return subportfolio

    @staticmethod
    def delete_subportfolio(subportfolio: SubPortfolio):
        """
        Deletes a SubPortfolio and its associated schema.
        """
        Schema.objects.filter(subportfolio=subportfolio).delete()
        subportfolio.delete()
