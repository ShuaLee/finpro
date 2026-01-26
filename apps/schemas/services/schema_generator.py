from django.db import transaction
from django.db.models import Prefetch
from django.core.exceptions import ValidationError

from schemas.models import Schema
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.template import SchemaTemplate
from schemas.services.schema_expansion_service import SchemaExpansionService


class SchemaGenerator:
    """
    Builds schemas from SchemaTemplates.

    Used ONLY when:
        - an account is created
        - no schema exists yet for (portfolio, account_type)
    """

    def __init__(self, *, portfolio, account_type):
        self.portfolio = portfolio
        self.account_type = account_type

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================
    @transaction.atomic
    def initialize(self) -> Schema:
        """
        Create schema if missing and populate from template.
        """
        from schemas.services.scv_refresh_service import SCVRefreshService

        # --------------------------------------------------
        # 1. Reuse schema if it already exists
        # --------------------------------------------------
        schema = Schema.objects.filter(
            portfolio=self.portfolio,
            account_type=self.account_type,
        ).first()

        if schema:
            return schema

        # --------------------------------------------------
        # 2. Select SchemaTemplate
        # --------------------------------------------------
        template = self._select_template()
        if not template:
            raise ValidationError(
                f"No SchemaTemplate available for account_type="
                f"{self.account_type.slug}"
            )

        # --------------------------------------------------
        # 3. Create Schema
        # --------------------------------------------------
        schema = Schema.objects.create(
            portfolio=self.portfolio,
            account_type=self.account_type,
        )

        # --------------------------------------------------
        # 4. Expand DEFAULT system columns
        # --------------------------------------------------
        default_templates = (
            template.columns
            .filter(is_default=True, is_system=True)
            .order_by("display_order", "id")
        )

        for template_column in default_templates:
            SchemaExpansionService.add_system_column(
                schema=schema,
                template_column=template_column,
            )

        # --------------------------------------------------
        # 5. Single recompute
        # --------------------------------------------------
        SCVRefreshService.schema_changed(schema)

        return schema

    # ==========================================================
    # INTERNAL HELPERS
    # ==========================================================
    def _select_template(self) -> SchemaTemplate | None:
        """
        Select schema template in priority order:

        1. Active template for account_type
        2. Active BASE template (account_type is NULL)
        """

        # Exact match first
        template = (
            SchemaTemplate.objects
            .filter(
                account_type=self.account_type,
                is_active=True,
            )
            .prefetch_related(
                Prefetch(
                    "columns",
                    queryset=SchemaColumnTemplate.objects.order_by(
                        "display_order", "id"
                    ),
                )
            )
            .first()
        )

        if template:
            return template

        # Fallback to BASE template
        return (
            SchemaTemplate.objects
            .filter(
                account_type__isnull=True,
                is_active=True,
                is_base=True,
            )
            .prefetch_related(
                Prefetch(
                    "columns",
                    queryset=SchemaColumnTemplate.objects.order_by(
                        "display_order", "id"
                    ),
                )
            )
            .first()
        )
