from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from schemas.models.template import SchemaTemplateColumn
from schemas.models.schema import SchemaColumn
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class SchemaColumnFactory:
    """
    Handles creation of SchemaColumns from:
      - SchemaTemplateColumns (predefined)
      - User-defined custom definitions
    """

    @staticmethod
    def _finalize_column(column):
        """Attach constraints and holding values after column creation."""
        SchemaConstraintManager.create_from_master(column)
        SchemaColumnValueManager.ensure_for_column(column)
        return column

    @staticmethod
    def add_from_template(schema, template_column_id):
        """
        Copy a SchemaTemplateColumn into the given Schema.
        """
        template_col = SchemaTemplateColumn.objects.get(id=template_column_id)

        # ensure account_type alignment
        if schema.account_type != template_col.template.account_type:
            raise ValueError(
                f"Template column belongs to '{template_col.template.account_type}', "
                f"but schema is '{schema.account_type}'."
            )

        # determine next display order
        max_order = schema.columns.aggregate(
            max_order=models.Max("display_order")).get("max_order") or 0

        # create SchemaColumn
        column = SchemaColumn.objects.create(
            schema=schema,
            title=template_col.title,
            identifier=template_col.identifier,
            data_type=template_col.data_type,
            source=template_col.source,
            source_field=template_col.source_field,
            is_editable=template_col.is_editable,
            is_deletable=True,
            is_system=template_col.is_system,
            display_order=max_order + 1,
        )

        return SchemaColumnFactory._finalize_column(column)

    # -------------------------------------
    # Custom User-Defined Columns
    # -------------------------------------
    @staticmethod
    def add_custom_column(schema, title: str, data_type: str):
        """
        Create a user-defined (custom) column in a schema.
        Automatically generates a safe identifier and attaches default constraints.
        """
        if not title or not data_type:
            raise ValidationError("Both 'title' and 'data_type' are required.")

        identifier = slugify(title)
        existing_ids = set(schema.columns.values_list("identifier", flat=True))
        if identifier in existing_ids:
            raise ValidationError(
                f"A column with identifier '{identifier}' already exists in this schema."
            )

        next_order = (schema.columns.aggregate(models.Max(
            "display_order"))["display_order__max"] or 0) + 1

        column = SchemaColumn.objects.create(
            schema=schema,
            title=title,
            identifier=identifier,
            data_type=data_type,
            source="custom",
            source_field=None,
            is_editable=True,
            is_deletable=True,
            is_system=False,
            display_order=next_order,
        )

        return SchemaColumnFactory._finalize_column(column)
