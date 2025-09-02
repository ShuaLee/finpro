from django.core.exceptions import ValidationError
from django.db import models
from schemas.models import SchemaColumn, SchemaColumnTemplate, SubPortfolioSchemaLink


class SchemaColumnAdder:
    def __init__(self, schema):
        self.schema = schema
        self.link = SubPortfolioSchemaLink.objects.filter(
            schema=schema).first()
        if not self.link:
            raise ValidationError("Schema is not linked to any account model.")

    def add_from_template(self, template: SchemaColumnTemplate):
        """
        Add a column from a template, recursively ensuring all formula dependencies
        are satisfied (by source_field).
        """
        formula = template.formula
        if formula and formula.dependencies:
            for dep in formula.dependencies:
                # 🔑 Always resolve dependencies by source_field
                if not self.schema.columns.filter(source_field=dep).exists():
                    dep_template = SchemaColumnTemplate.objects.filter(
                        schema_type=self.schema.schema_type,
                        account_model_ct=self.link.account_model_ct,
                        source_field=dep,
                    ).first()

                    if not dep_template:
                        raise ValidationError(
                            f"Missing template for dependency '{dep}'"
                        )

                    # Recursively add dependency first
                    self.add_from_template(dep_template)

        # Already exists?
        existing = self.schema.columns.filter(
            source_field=template.source_field).first()
        if existing:
            return existing, False  # 🚨 indicate not created

        column = SchemaColumn.objects.create(
            schema=self.schema,
            template=template,
            formula=template.formula,
            source=template.source,
            source_field=template.source_field,
            title=template.title,
            data_type=template.data_type,
            field_path=template.field_path,
            is_editable=template.is_editable,
            is_deletable=template.is_deletable,
            is_system=template.is_system,
            constraints=template.constraints,
            display_order=template.display_order,
        )
        return column, True  # ✅ indicate created

    def add_custom_column(self, title, data_type, constraints=None):
        return SchemaColumn.objects.create(
            schema=self.schema,
            title=title,
            data_type=data_type,
            source="custom",
            constraints=constraints or {},
            is_editable=True,
            is_deletable=True,
            is_system=False,
        )
    
    def add_calculated_column(self, title, formula):
        """
        Add a calculated column that references an existing Formula.
        Validates dependencies exist in the schema.
        """
        missing = [
            dep for dep in (formula.dependencies or [])
            if not self.schema.columns.filter(identifier=dep).exists()
        ]
        if missing:
            raise ValidationError(
                f"❌ Cannot create calculated column. "
                f"Missing dependencies in schema: {', '.join(missing)}"
            )

        # Already exists?
        existing = self.schema.columns.filter(
            formula=formula, title=title
        ).first()
        if existing:
            return existing, False

        column = SchemaColumn.objects.create(
            schema=self.schema,
            formula=formula,
            source="calculated",
            title=title,
            data_type="decimal",
            is_editable=False,
            is_deletable=True,
            is_system=False,
        )
        return column, True
    
    def validate_dependencies(self, identifiers):
        """Ensure all identifiers exist in this schema."""
        missing = [
            dep for dep in identifiers
            if not self.schema.columns.filter(identifier=dep).exists()
        ]
        if missing:
            raise ValidationError(
                f"❌ Cannot create calculated column. Missing dependencies in schema: {', '.join(missing)}"
            )
