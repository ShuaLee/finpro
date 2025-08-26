from django.core.exceptions import ValidationError
from schemas.models import SchemaColumn, SchemaColumnTemplate


class SchemaColumnAdder:
    def __init__(self, schema):
        self.schema = schema

    def column_exists(self, template: SchemaColumnTemplate) -> bool:
        return SchemaColumn.objects.filter(
            schema=self.schema,
            source=template.source,
            source_field=template.source_field
        ).exists()

    def add_from_template(self, template: SchemaColumnTemplate) -> SchemaColumn:
        if self.column_exists(template):
            raise ValidationError(
                f"Column from template '{template.title}' already exists in schema.")

        column = SchemaColumn(
            schema=self.schema,
            title=template.title,
            data_type=template.data_type,
            source=template.source,
            source_field=template.source_field,
            field_path=template.field_path,
            is_editable=template.is_editable,
            is_deletable=template.is_deletable,
            is_system=template.is_system,
            formula_method=template.formula_method,
            formula_expression=template.formula_expression,
            constraints=template.constraints,
        )
        column.save()
        return column

    def add_custom_column(self, title, data_type, **kwargs) -> SchemaColumn:
        if data_type not in ["decimal", "string"]:
            raise ValidationError(
                "Only decimal and string custom columns are allowed.")

        column = SchemaColumn(
            schema=self.schema,
            title=title,
            data_type=data_type,
            source="custom",
            is_editable=True,
            is_deletable=True,
            is_system=False,
            constraints=kwargs.get("constraints", {}),
            custom_title=kwargs.get("custom_title", None),
        )

        column.save()
        return column

    @staticmethod
    def get_available_schema_column_templates(schema):
        """
        Fetches all templates for the schema's type and account model,
        and flags which ones are already active in the schema.
        """
        active_columns = set(
            SchemaColumn.objects
            .filter(schema=schema, is_system=True)
            .values_list("source", "source_field")
        )

        templates = SchemaColumnTemplate.objects.filter(
            schema_type=schema.schema_type,
            # Optional, if you want to filter by account type
            account_model_ct=schema.content_type
        )

        # Dynamically tag each template with is_active (not saved to DB)
        for tpl in templates:
            tpl.is_active = (tpl.source, tpl.source_field) in active_columns

        return templates
