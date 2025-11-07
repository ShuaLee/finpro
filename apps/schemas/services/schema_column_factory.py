from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from schemas.models.template import SchemaTemplateColumn
from schemas.models.schema import SchemaColumn
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class SchemaColumnFactory:
    """Handles creation of SchemaColumns from templates or user-defined definitions."""

    @staticmethod
    def _finalize_column(column):
        SchemaConstraintManager.create_from_master(column)
        SchemaColumnValueManager.ensure_for_column(column)
        return column

    # ---------------------------
    # From Template
    # ---------------------------
    @staticmethod
    def add_from_template(schema, template_column_id):
        template_col = SchemaTemplateColumn.objects.get(id=template_column_id)

        # Ensure account type alignment
        if schema.account_type != template_col.template.account_type:
            raise ValidationError(
                f"Template column belongs to '{template_col.template.account_type}', "
                f"but schema is '{schema.account_type}'."
            )

        # Prevent duplicates
        if schema.columns.filter(identifier=template_col.identifier).exists():
            raise ValidationError(
                f"The column '{template_col.title}' already exists in this schema."
            )

        max_order = schema.columns.aggregate(models.Max("display_order"))[
            "display_order__max"] or 0

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

    # ---------------------------
    # Custom Column
    # ---------------------------
    @staticmethod
    def add_custom_column(schema, title: str, data_type: str):
        if not title or not data_type:
            raise ValidationError("Both 'title' and 'data_type' are required.")

        base_identifier = slugify(title)
        existing_ids = set(schema.columns.values_list("identifier", flat=True))

        # Ensure identifier uniqueness
        identifier = base_identifier
        counter = 1
        while identifier in existing_ids:
            counter += 1
            identifier = f"{base_identifier}_{counter}"

        # Optional: warn if duplicate title
        if counter > 1:
            raise ValidationError(
                f"A column with the title '{title}' already exists. Please choose a unique name."
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

    @staticmethod
    def delete_column(column):
        """
        Deletes a SchemaColumn safely.
        Resequencing is handled automatically by the model's delete().
        """
        column.delete()
