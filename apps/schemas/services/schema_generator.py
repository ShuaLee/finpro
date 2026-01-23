from django.db import transaction
from django.db.models import Prefetch

from schemas.models import Schema, SchemaColumn, SchemaTemplate, SchemaColumnTemplate
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.scv_refresh_service import SCVRefreshService


class SchemaGenerator:
    """
    Builds schemas from SchemaTemplates.

    Used ONLY when:
        - an account is created
        - a schema does not yet exist
    """

    def __init__(self, *, portfolio, account_type):
        self.portfolio = portfolio
        self.account_type = account_type

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================
    @transaction.atomic
    def initialize(self):
        template = (
            SchemaTemplate.objects
            .filter(account_type=self.account_type, is_active=True)
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

        if not template:
            raise ValueError(
                f"No active SchemaTemplate for account_type={self.account_type.slug}"
            )

        schema, _ = Schema.objects.get_or_create(
            portfolio=self.portfolio,
            account_type=self.account_type,
        )

        for tcol in template.columns.filter(is_default=True):
            column = SchemaColumn.objects.create(
                schema=schema,
                title=tcol.title,
                identifier=tcol.identifier,
                data_type=tcol.data_type,
                source=tcol.source,
                source_field=(
                    None if tcol.source == "formula" else tcol.source_field
                ),
                formula_definition=tcol.formula_definition,
                is_editable=tcol.is_editable,
                is_deletable=tcol.is_deletable,
                is_system=True,
                display_order=tcol.display_order,
            )

            SchemaConstraintManager.create_from_master(
                column,
                overrides=tcol.constraints or {},
            )

            SchemaColumnValueManager.ensure_for_column(column)

        # Single recompute after creation
        SCVRefreshService.schema_changed(schema)

        return schema
