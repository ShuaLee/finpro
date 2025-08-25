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
            is_default=template.is_default,
            is_deletable=template.is_deletable,
            is_system=template.is_system,
            formula_method=template.formula_method,
            formula_expression=template.formula_expression,
            constraints=template.constraints,
            investment_theme=template.investment_theme,
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
