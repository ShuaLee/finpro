from django.db import transaction
from django.core.exceptions import ValidationError

from schemas.models import Schema
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.services.schema_expansion_service import SchemaExpansionService
from schemas.policies.default_schema_policy import DefaultSchemaPolicy


class SchemaGenerator:
    """
    Builds schemas from system column templates + default policy.

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
        Create schema if missing and populate with default system columns.
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
        # 2. Create empty Schema
        # --------------------------------------------------
        schema = Schema.objects.create(
            portfolio=self.portfolio,
            account_type=self.account_type,
        )

        # --------------------------------------------------
        # 3. Resolve default column identifiers (POLICY)
        # --------------------------------------------------
        identifiers = DefaultSchemaPolicy.default_identifiers_for_account_type(
            self.account_type
        )

        if not identifiers:
            # Valid: custom / empty schema
            return schema

        # --------------------------------------------------
        # 4. Expand system columns
        # --------------------------------------------------
        templates = SchemaColumnTemplate.objects.filter(
            identifier__in=identifiers,
            is_system=True,
        )

        found = set(t.identifier for t in templates)
        missing = set(identifiers) - found

        if missing:
            raise ValidationError(
                f"Missing system SchemaColumnTemplates: {sorted(missing)}"
            )

        # Preserve order defined by policy
        template_by_id = {t.identifier: t for t in templates}

        for identifier in identifiers:
            SchemaExpansionService.add_system_column(
                schema=schema,
                template_column=template_by_id[identifier],
            )

        # --------------------------------------------------
        # 5. Single recompute
        # --------------------------------------------------
        SCVRefreshService.schema_changed(schema)

        return schema
