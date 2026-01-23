from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.text import slugify

from schemas.models.schema_column import SchemaColumn
from schemas.models.template import SchemaColumnTemplate
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.schema_expansion_service import SchemaExpansionService
from schemas.services.scv_refresh_service import SCVRefreshService


class SchemaColumnFactory:
    """
    Entry point for creating SchemaColumns.

    Handles:
        - system template columns
        - user-defined custom columns
        - identifier safety
        - constraint attachment
        - SCV initialization

    ❗ All recomputation is delegated to SCVRefreshService.
    """

    # ==========================================================
    # INTERNAL HELPERS
    # ==========================================================
    @staticmethod
    def _next_display_order(schema):
        return (
            schema.columns.aggregate(
                max=models.Max("display_order")
            ).get("max") or 0
        ) + 1

    @staticmethod
    def _ensure_unique_identifier(schema, base_identifier: str) -> str:
        existing = set(schema.columns.values_list("identifier", flat=True))

        identifier = base_identifier
        counter = 1

        while identifier in existing:
            identifier = f"{base_identifier}_{counter}"
            counter += 1

        return identifier

    # ==========================================================
    # SYSTEM / TEMPLATE COLUMNS
    # ==========================================================
    @staticmethod
    @transaction.atomic
    def add_from_template(schema, template_column: SchemaColumnTemplate):
        """
        Add a system column from a SchemaTemplateColumn.

        Delegates dependency handling to SchemaExpansionService.
        """

        if not template_column.is_system:
            raise ValidationError(
                "Only system template columns may be added via this method."
            )

        # Structural expansion (recursive, safe)
        column = SchemaExpansionService.add_system_column(
            schema=schema,
            template_column=template_column,
        )

        return column

    # ==========================================================
    # CUSTOM USER COLUMNS
    # ==========================================================
    @staticmethod
    @transaction.atomic
    def add_custom_column(
        *,
        schema,
        title: str,
        data_type: str,
        identifier_override: str | None = None,
    ):
        """
        Create a user-defined custom column.
        """

        if not title:
            raise ValidationError("Column title is required.")

        if not data_type:
            raise ValidationError("Column data_type is required.")

        base_identifier = slugify(identifier_override or title)
        if not base_identifier:
            raise ValidationError("Could not derive a valid identifier.")

        identifier = SchemaColumnFactory._ensure_unique_identifier(
            schema,
            base_identifier,
        )

        column = SchemaColumn.objects.create(
            schema=schema,
            title=title,
            identifier=identifier,
            data_type=data_type,
            source=SchemaColumn.Source.CUSTOM,
            source_field=None,
            formula_definition=None,
            is_editable=True,
            is_deletable=True,
            is_system=False,
            display_order=SchemaColumnFactory._next_display_order(schema),
        )

        # Attach constraints
        SchemaConstraintManager.create_from_master(column)

        # Ensure SCVs exist (no recompute)
        SchemaColumnValueManager.ensure_for_column(column)

        # Single recompute
        SCVRefreshService.schema_changed(schema)

        return column

    # ==========================================================
    # DELETE COLUMN
    # ==========================================================
    @staticmethod
    @transaction.atomic
    def delete_column(column: SchemaColumn):
        """
        Delete a column safely and trigger recomputation.
        """

        if not column.is_deletable:
            raise ValidationError("This column cannot be deleted.")

        schema = column.schema
        column.delete()

        SCVRefreshService.schema_changed(schema)

    # ==========================================================
    # ENSURE COLUMN (IDEMPOTENT)
    # ==========================================================
    @staticmethod
    def ensure_column(
        *,
        schema,
        identifier: str,
        title: str,
        data_type: str,
    ):
        """
        Ensure a column exists with the given identifier.
        """
        existing = schema.columns.filter(identifier=identifier).first()
        if existing:
            if existing.data_type != data_type:
                raise ValidationError(
                    f"Column '{identifier}' exists but has data_type "
                    f"{existing.data_type} (expected {data_type})."
                )
            return existing

        return SchemaColumnFactory.add_custom_column(
            schema=schema,
            title=title,
            data_type=data_type,
            identifier_override=identifier,
        )
