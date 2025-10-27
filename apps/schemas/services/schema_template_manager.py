from django.db import transaction
from django.utils import timezone

from schemas.models.schema import Schema, SchemaColumn
from schemas.models.template import SchemaTemplate
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.utils import normalize_constraints


class SchemaTemplateManager:
    """
    Handles applying SchemaTemplates to generate real Schemas.
    """

    @staticmethod
    @transaction.atomic
    def apply_template(portfolio, account_type, refresh=False):
        """
        Build (or rebuild) a Schema for a given portfolio/account_type
        from the global SchemaTemplate definition.

        Args:
            portfolio: Portfolio instance.
            account_type: str - account type code (e.g. 'equity_self').
            refresh: bool - if True, will delete existing columns first.

        Returns:
            Schema instance created or updated.
        """
        template = SchemaTemplate.objects.filter(
            account_type=account_type, is_active=True
        ).first()

        if not template:
            raise ValueError(
                f"No active SchemaTemplate found for '{account_type}'")

        # ✅ Ensure schema record exists for this portfolio/account type
        schema, _ = Schema.objects.update_or_create(
            portfolio=portfolio,
            account_type=account_type,
            defaults={"updated_at": timezone.now()},
        )

        # Optionally refresh by clearing existing columns
        if refresh:
            schema.columns.all().delete()

        # Avoid re-adding existing columns by identifier
        existing_ids = set(schema.columns.values_list("identifier", flat=True))

        for tcol in template.columns.all().order_by("display_order", "id"):
            if tcol.identifier in existing_ids:
                continue  # Skip if already exists (idempotent apply)

            col = SchemaColumn.objects.create(
                schema=schema,
                title=tcol.title,
                identifier=tcol.identifier,
                data_type=tcol.data_type,
                source=tcol.source,
                source_field=tcol.source_field,
                is_editable=tcol.is_editable,
                is_deletable=tcol.is_deletable,
                is_system=tcol.is_system,
                constraints=normalize_constraints(
                    tcol.default_constraints or {}),
                display_order=tcol.display_order,
            )

            # ✅ Auto-generate constraints and default column values
            SchemaConstraintManager.create_from_master(col)
            SchemaColumnValueManager.ensure_for_column(col)

        return schema
