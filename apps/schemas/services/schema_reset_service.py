from django.db import transaction
from django.core.exceptions import ValidationError

from schemas.models import SchemaColumn
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.services.schema_expansion_service import SchemaExpansionService
from schemas.services.scv_refresh_service import SCVRefreshService
from schemas.policies.default_schema_policy import DefaultSchemaPolicy


class SchemaResetService:
    """
    Reset a Schema to its system default structure.

    What this does:
        - Removes ALL schema columns
        - Rebuilds system columns from default policy
        - Recomputes SCVs once

    What this does NOT do:
        - Modify SchemaColumnTemplates
        - Modify FormulaDefinitions
        - Modify user holdings
    """

    @staticmethod
    @transaction.atomic
    def reset_to_default(schema):
        """
        Reset the given schema to its default system columns.
        """

        account_type = schema.account_type

        # --------------------------------------------------
        # 1. Resolve default column identifiers
        # --------------------------------------------------
        identifiers = DefaultSchemaPolicy.default_identifiers_for_account_type(
            account_type
        )

        # --------------------------------------------------
        # 2. Delete ALL existing schema columns
        # --------------------------------------------------
        SchemaColumn.objects.filter(schema=schema).delete()

        if not identifiers:
            # Valid: empty schema
            SCVRefreshService.schema_changed(schema)
            return schema

        # --------------------------------------------------
        # 3. Resolve system column templates
        # --------------------------------------------------
        templates = SchemaColumnTemplate.objects.filter(
            identifier__in=identifiers,
            is_system=True,
        )

        found = {t.identifier for t in templates}
        missing = set(identifiers) - found

        if missing:
            raise ValidationError(
                f"Missing system SchemaColumnTemplates: {sorted(missing)}"
            )

        template_by_id = {t.identifier: t for t in templates}

        # --------------------------------------------------
        # 4. Rebuild schema structure
        # --------------------------------------------------
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
