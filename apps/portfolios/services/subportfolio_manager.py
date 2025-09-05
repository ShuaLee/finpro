from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.text import slugify

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
            name (str, optional): Custom name (mainly for custom type).
            slug (str, optional): Slug (mainly for custom type).
            schema_name_fn (callable, optional): Custom schema name formatter.

        Returns:
            SubPortfolio
        """
        if type not in SUBPORTFOLIO_CONFIG:
            raise ValidationError(f"Unknown subportfolio type: {type}")

        cfg = SUBPORTFOLIO_CONFIG[type]

        with transaction.atomic():
            # 🚦 1. Uniqueness check (only one stock/crypto/metal per portfolio)
            if cfg.get("unique", False):
                if SubPortfolio.objects.filter(portfolio=portfolio, type=type).exists():
                    raise ValidationError(
                        f"{cfg['default_name']} already exists for this portfolio."
                    )

            # 🆕 2. Auto-generate name/slug if not provided
            final_name = name or cfg.get(
                "default_name", f"{type.capitalize()} Portfolio")
            final_slug = slug or slugify(final_name)

            # 3. Create SubPortfolio row
            subportfolio = SubPortfolio.objects.create(
                portfolio=portfolio, type=type, name=final_name, slug=final_slug
            )

            # 🔁 4. Get account models for this type (from registry)
            account_model_map = get_account_model_map(cfg["schema_type"])

            # 🛠 5. Generate schema(s) via SchemaGenerator
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
