from django.core.exceptions import ValidationError
from schemas.models import SchemaColumn, SchemaColumnTemplate, SubPortfolioSchemaLink
from schemas.services.initialize_column_values import initialize_column_values


class SchemaColumnAdder:
    def __init__(self, schema):
        self.schema = schema
        self.link = SubPortfolioSchemaLink.objects.filter(
            schema=schema).first()
        if not self.link:
            raise ValidationError("Schema is not linked to any account model.")

    def _get_accounts(self):
        """
        Get all accounts/holdings linked to this schema's portfolio.
        Assumes schema.portfolio exposes a .holdings or .accounts relation.
        """
        portfolio = self.schema.portfolio
        if hasattr(portfolio, "holdings"):
            return portfolio.holdings.all()
        if hasattr(portfolio, "accounts"):
            return portfolio.accounts.all()
        return []

    def add_from_template(self, template: SchemaColumnTemplate):
        """
        Add a column from a template, recursively ensuring all formula dependencies
        are satisfied (by source_field).
        """
        formula = template.formula
        if formula and formula.dependencies:
            for dep in formula.dependencies:
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
                    self.add_from_template(dep_template)

        existing = self.schema.columns.filter(
            source_field=template.source_field).first()
        if existing:
            return existing, False

        column = SchemaColumn.objects.create(
            schema=self.schema,
            template=template,
            formula=template.formula,  # ✅ system/global formulas only
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

        # 🔑 initialize values
        initialize_column_values(column, self._get_accounts())

        return column, True

    def add_custom_column(self, title, data_type, constraints=None):
        column = SchemaColumn.objects.create(
            schema=self.schema,
            title=title,
            data_type=data_type,
            source="custom",
            constraints=constraints or {},
            is_editable=True,
            is_deletable=True,
            is_system=False,
        )

        # 🔑 initialize values
        initialize_column_values(column, self._get_accounts())

        return column

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

        existing = self.schema.columns.filter(
            formula=formula, title=title).first()
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

        # 🔑 initialize values
        initialize_column_values(column, self._get_accounts())

        return column, True

    def validate_dependencies(self, identifiers):
        """Ensure all identifiers exist in this schema."""
        missing = [
            dep for dep in identifiers
            if not self.schema.columns.filter(identifier=dep).exists()
        ]
        if missing:
            raise ValidationError(
                f"❌ Cannot create calculated column. "
                f"Missing dependencies in schema: {', '.join(missing)}"
            )
