from django.db import transaction
from schemas.models.schema import Schema
from schemas.services.schema_template_manager import SchemaTemplateManager
from core.types import get_domain_meta
import logging

logger = logging.getLogger(__name__)


class SchemaGenerator:
    """
    High-level orchestrator that builds portfolio schemas based on available
    SchemaTemplates. Falls back to domain_meta configs if no templates exist.
    """

    def __init__(self, portfolio, domain_type: str):
        self.portfolio = portfolio
        self.domain_type = domain_type
        self.schema = None

    # -------------------------------
    # Main Initialization
    # -------------------------------
    @transaction.atomic
    def initialize(self, custom_schema_namer=None):
        """
        Build one schema per account_type for this portfolio’s domain.

        ✅ Uses SchemaTemplate if available (preferred)
        ⚙️  Falls back to domain_meta if no templates are found.
        """
        logger.debug(
            f"🧱 Initializing schema for portfolio={self.portfolio.id}, domain={self.domain_type}")

        domain_meta = get_domain_meta(self.domain_type)
        account_types = domain_meta.get("account_types", [])
        schema_config = domain_meta.get("schema_config", {})

        if not account_types:
            raise ValueError(
                f"No account types registered for domain {self.domain_type}")

        for account_type in account_types:
            user_email = self.portfolio.profile.user.email
            schema_name = (
                custom_schema_namer(self.portfolio, account_type)
                if custom_schema_namer
                else f"{user_email}'s {self.domain_type.title()} ({account_type}) Schema"
            )

            logger.info(
                f"📄 Generating schema for {account_type}: {schema_name}")

            # Try to build from SchemaTemplate first
            try:
                self.schema = SchemaTemplateManager.apply_template(
                    self.portfolio, account_type)
                logger.info(
                    f"✅ Created schema from template for {account_type}")
                continue  # Template found — skip fallback logic

            except ValueError:
                logger.warning(
                    f"⚠️ No template found for {account_type}, falling back to domain_meta config")

            # --- FALLBACK TO OLD CONFIG ---
            self.schema, _ = Schema.objects.update_or_create(
                portfolio=self.portfolio,
                account_type=account_type,
                defaults={},
            )

            for source, field_defs in schema_config.items():
                for source_field, col_def in field_defs.items():
                    if not col_def.get("is_default"):
                        continue
                    self._add_column_from_config(source, source_field, col_def)

        logger.info(
            f"🎉 Finished schema initialization for portfolio={self.portfolio.id}")
        return self.schema

    # -------------------------------
    # Legacy Config Fallback
    # -------------------------------
    def _add_column_from_config(self, source, source_field, col_def):
        """
        Only used when SchemaTemplate is unavailable.
        """
        from schemas.models.schema import SchemaColumn
        from schemas.utils import normalize_constraints
        from schemas.services.schema_constraint_manager import SchemaConstraintManager
        from schemas.services.schema_column_value_manager import SchemaColumnValueManager

        col = SchemaColumn.objects.create(
            schema=self.schema,
            title=col_def["title"],
            identifier=f"{source}_{source_field}".lower(),
            data_type=col_def["data_type"],
            source=source,
            source_field=source_field,
            is_editable=col_def.get("is_editable", True),
            is_deletable=col_def.get("is_deletable", True),
            is_system=col_def.get("is_system", False),
            constraints=normalize_constraints(col_def.get("constraints", {})),
            display_order=col_def.get("display_order", 0),
        )

        SchemaConstraintManager.create_from_master(col)
        SchemaColumnValueManager.ensure_for_column(col)
        logger.debug(f"➕ Added fallback column: {col.title}")
