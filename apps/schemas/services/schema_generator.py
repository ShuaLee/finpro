# schemas/services/schema_generator.py

from django.db.models import Prefetch
from django.utils.text import slugify

from schemas.models.schema import Schema, SchemaColumn
from schemas.models.template import SchemaTemplate, SchemaTemplateColumn
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from schemas.services.schema_column_value_manager import SchemaColumnValueManager

import logging
logger = logging.getLogger(__name__)


class SchemaGenerator:
    """
    Builds schemas for a portfolio.

    Flow:
        SchemaTemplate → SchemaColumn → SchemaConstraint → SchemaColumnValue
    """

    def __init__(self, portfolio, domain_type):
        self.portfolio = portfolio
        self.domain_type = domain_type

    # =====================================================================
    # MAIN ENTRY
    # =====================================================================
    def initialize(self, custom_schema_namer=None):
        account_type = self.domain_type

        logger.info(
            f"📄 Generating schema for account_type={account_type.slug}"
        )

        template = (
            SchemaTemplate.objects.filter(
                account_type=account_type,
                is_active=True,
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

        if not template:
            raise ValueError(
                f"No active SchemaTemplate found for account type '{account_type.slug}'."
            )

        schema = self._create_from_template(template)

        logger.info(
            f"🎉 Schema initialization complete for portfolio={self.portfolio.id}, "
            f"account_type={account_type.slug}"
        )

        return [schema]

    # =====================================================================
    # TEMPLATE → SCHEMA
    # =====================================================================
    def _create_from_template(self, template: SchemaTemplate):
        schema, _ = Schema.objects.update_or_create(
            portfolio=self.portfolio,
            account_type=template.account_type,
            defaults={},
        )

        template_columns = template.columns.filter(
            is_default=True
        ).order_by("display_order", "id")

        from schemas.models.formula import Formula

        for tcol in template_columns:
            formula_obj = None

            if tcol.source == "formula":
                if not tcol.source_field:
                    raise ValueError(
                        f"Template column '{tcol.identifier}' is marked as formula "
                        f"but has no source_field."
                    )

                formula_obj = Formula.objects.filter(
                    identifier=tcol.source_field
                ).first()

                if not formula_obj:
                    raise ValueError(
                        f"Formula '{tcol.source_field}' does not exist."
                    )

            column = SchemaColumn.objects.create(
                schema=schema,
                title=tcol.title,
                identifier=self._safe_identifier(tcol.identifier, schema),
                data_type=tcol.data_type,
                source=tcol.source,
                source_field=None if tcol.source == "formula" else tcol.source_field,
                formula=formula_obj,
                is_editable=tcol.is_editable,
                is_deletable=tcol.is_deletable,
                is_system=tcol.is_system,
                display_order=tcol.display_order,
            )

            overrides = dict(tcol.constraints or {})
            SchemaConstraintManager.create_from_master(column, overrides)
            SchemaColumnValueManager.ensure_for_column(column)

            logger.debug(
                f"➕ Added column '{column.title}' (order {column.display_order})"
            )

        # 🔑 SINGLE schema-wide recompute
        from schemas.services.scv_refresh_service import SCVRefreshService
        SCVRefreshService.schema_changed(schema)

        return schema

    # =====================================================================
    # UNIQUE IDENTIFIER
    # =====================================================================
    def _safe_identifier(self, base_identifier: str, schema: Schema) -> str:
        identifier = slugify(base_identifier)
        existing = set(schema.columns.values_list("identifier", flat=True))

        if identifier not in existing:
            return identifier

        original = identifier
        counter = 1
        while identifier in existing:
            counter += 1
            identifier = f"{original}_{counter}"

        return identifier
