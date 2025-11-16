from django.db import transaction
from django.db.models import Prefetch
from django.utils.text import slugify
from schemas.models.schema import Schema, SchemaColumn
from schemas.models.template import SchemaTemplate, SchemaTemplateColumn
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from core.types import get_domain_meta
import logging

logger = logging.getLogger(__name__)


class SchemaGenerator:
    """
    🔧 Builds schemas for a portfolio.
    Uses SchemaTemplateColumns (preferred) or legacy config (fallback).
    """

    def __init__(self, portfolio, domain_type: str):
        self.portfolio = portfolio
        self.domain_type = domain_type

    # ------------------------------------------------
    # Main Initialization
    # ------------------------------------------------
    @transaction.atomic
    def initialize(self, custom_schema_namer=None):
        logger.info(
            f"🧱 Initializing schemas for portfolio={self.portfolio.id}, domain={self.domain_type}"
        )

        domain_meta = get_domain_meta(self.domain_type)
        account_types = domain_meta.get("account_types", [])
        schema_config = domain_meta.get("schema_config", {})

        if not account_types:
            raise ValueError(
                f"No account types registered for domain '{self.domain_type}'"
            )

        schemas = []

        for account_type in account_types:
            schema_name = (
                custom_schema_namer(self.portfolio, account_type)
                if custom_schema_namer
                else f"{self.portfolio.profile.user.email}'s {self.domain_type.title()} ({account_type}) Schema"
            )

            logger.info(f"📄 Generating schema for account_type={account_type}")

            template = (
                SchemaTemplate.objects.filter(
                    account_type=account_type, is_active=True
                )
                .prefetch_related(
                    Prefetch(
                        "columns",
                        queryset=SchemaTemplateColumn.objects.order_by(
                            "display_order", "id"
                        ),
                    )
                )
                .first()
            )

            if template:
                schema = self._create_from_template(template)
                schemas.append(schema)
                logger.info(
                    f"✅ Created schema from template for {account_type}")
                continue

            # fallback path
            logger.warning(
                f"⚠️ No SchemaTemplate for {account_type}, falling back to legacy schema config."
            )
            schema = self._create_from_legacy_config(
                account_type, schema_config)
            schemas.append(schema)

        logger.info(
            f"🎉 Schema initialization complete for portfolio={self.portfolio.id}"
        )
        return schemas

    # ------------------------------------------------
    # Template-based schema creation
    # ------------------------------------------------
    def _create_from_template(self, template: SchemaTemplate):

        schema, created = Schema.objects.update_or_create(
            portfolio=self.portfolio,
            account_type=template.account_type,
            defaults={},
        )

        template_columns = template.columns.filter(is_default=True).order_by(
            "display_order", "id"
        )

        logger.debug(
            f"🧩 Creating {template_columns.count()} columns for schema {schema.account_type}"
        )

        for tcol in template_columns:

            column = SchemaColumn.objects.create(
                schema=schema,
                title=tcol.title,
                identifier=self._safe_identifier(tcol.identifier, schema),
                data_type=tcol.data_type,
                source=tcol.source,
                source_field=tcol.source_field,
                is_editable=tcol.is_editable,
                is_deletable=tcol.is_deletable,
                is_system=tcol.is_system,
                display_order=tcol.display_order,
            )

            # 👇 This is the important line: send the JSON constraints into the constraint manager
            overrides = tcol.constraints or {}

            SchemaConstraintManager.create_from_master(column, overrides)
            SchemaColumnValueManager.ensure_for_column(column)

            logger.debug(
                f"➕ Added column '{column.title}' (order {column.display_order})"
            )

        return schema

    # ------------------------------------------------
    # Identifier utility
    # ------------------------------------------------
    def _safe_identifier(self, base_identifier: str, schema: Schema) -> str:
        identifier = slugify(base_identifier)
        existing = set(schema.columns.values_list("identifier", flat=True))

        if identifier not in existing:
            return identifier

        # ensure uniqueness by suffixing
        original = identifier
        counter = 1
        while identifier in existing:
            counter += 1
            identifier = f"{original}_{counter}"

        return identifier
