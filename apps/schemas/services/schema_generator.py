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
    🔧 Builds schemas for a portfolio.

    Flow:
        SchemaTemplate → SchemaColumn → SchemaConstraint → SchemaColumnValue

    - Holding stores RAW values (no rounding)
    - SCV is the formatted display layer (rounded)
    - Per-asset precision comes from CryptoDetail
    """

    def __init__(self, portfolio, domain_type):
        self.portfolio = portfolio
        self.domain_type = domain_type  # AccountType instance

    # =====================================================================
    # MAIN ENTRY
    # =====================================================================
    def initialize(self, custom_schema_namer=None):
        """
        Build a schema for ONE account_type (self.domain_type),
        which is already an AccountType instance.
        """
        account_type = self.domain_type

        schema_name = (
            custom_schema_namer(self.portfolio, account_type)
            if custom_schema_namer
            else f"{self.portfolio.profile.user.email}'s {account_type.name} Schema"
        )

        logger.info(
            f"📄 Generating schema for account_type={account_type.slug}")

        template = (
            SchemaTemplate.objects.filter(
                account_type=account_type,
                is_active=True,
            )
            .prefetch_related(
                Prefetch(
                    "columns",
                    queryset=SchemaTemplateColumn.objects.order_by(
                        "display_order", "id"),
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
    # TEMPLATE → SCHEMA GENERATION
    # =====================================================================
    def _create_from_template(self, template: SchemaTemplate):
        schema, created = Schema.objects.update_or_create(
            portfolio=self.portfolio,
            account_type=template.account_type,
            defaults={},
        )

        template_columns = template.columns.filter(
            is_default=True).order_by("display_order", "id")
        logger.debug(
            f"🧩 Creating {template_columns.count()} columns for schema {schema.account_type}")

        from schemas.models.formula import Formula
        from schemas.services.formulas.update_engine import FormulaUpdateEngine

        formula_columns = []

        for tcol in template_columns:
            formula_obj = None

            if tcol.source == "formula":
                if not tcol.source_field:
                    raise ValueError(
                        f"Template column '{tcol.identifier}' is marked as formula "
                        f"but has no source_field (formula identifier)."
                    )

                formula_obj = Formula.objects.filter(
                    identifier=tcol.source_field).first()

                if not formula_obj:
                    raise ValueError(
                        f"SchemaTemplateColumn '{tcol.identifier}' references "
                        f"formula '{tcol.source_field}', but it does not exist."
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

            if column.source == "formula":
                formula_columns.append(column)

            logger.debug(
                f"➕ Added column '{column.title}' (order {column.display_order})")

        self._refresh_formula_columns(schema, formula_columns)

        return schema

    # =====================================================================
    # UNIQUE IDENTIFIER BUILDER
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

    # =====================================================================
    # REFRESH FORMULAS
    # =====================================================================
    def _refresh_formula_columns(self, schema, formula_columns):
        """
        Recompute all formula-based SCVs in this schema.
        """
        if not formula_columns:
            return

        from schemas.services.formulas.update_engine import FormulaUpdateEngine

        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        ).prefetch_related("holdings")

        for account in accounts:
            for holding in account.holdings.all():
                engine = FormulaUpdateEngine(holding, schema)

                for col in formula_columns:
                    engine.update_dependent_formulas(col.identifier)
