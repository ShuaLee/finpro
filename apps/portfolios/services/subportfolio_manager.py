from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from portfolios.models.portfolio import Portfolio
from portfolios.models.subportfolio import SubPortfolio
from schemas.models import Schema
from schemas.services.schema_generator import SchemaGenerator
from core.types import get_domain_meta


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
        """
        domain_meta = get_domain_meta(domain_type)

        with transaction.atomic():
            # 🚦 1. Uniqueness check
            if domain_meta.get("unique_subportfolio", False):
                if SubPortfolio.objects.filter(
                    portfolio=portfolio, type=domain_type
                ).exists():
                    raise ValidationError(
                        f"{domain_meta['default_subportfolio_name']} already exists for this portfolio."
                    )

            # 🆕 2. Auto-generate name/slug
            final_name = name or domain_meta.get(
                "default_subportfolio_name", f"{domain_type.capitalize()} Portfolio"
            )
            final_slug = slug or slugify(final_name)

            # 3. Create SubPortfolio row
            subportfolio = SubPortfolio.objects.create(
                portfolio=portfolio, type=domain_type, name=final_name, slug=final_slug
            )

            # 🛠 4. Generate schema(s) for this subportfolio
            generator = SchemaGenerator(subportfolio, domain_type)
            generator.initialize(custom_schema_namer=schema_name_fn)

            return subportfolio

    @staticmethod
    def delete_subportfolio(subportfolio: SubPortfolio):
        """
        Deletes a SubPortfolio and its associated schema(s).
        """
        Schema.objects.filter(subportfolio=subportfolio).delete()
        subportfolio.delete()
