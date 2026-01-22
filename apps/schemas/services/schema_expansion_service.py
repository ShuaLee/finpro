from django.core.exceptions import ValidationError
from django.db import transaction, models

from schemas.models.schema import SchemaColumn
from schemas.models.template import SchemaTemplateColumn
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.scv_refresh_service import SCVRefreshService


class SchemaExpansionService:
    """
    Explicitly expands a Schema by adding SYSTEM columns
    defined by SchemaTemplateColumns.

    This is the ONLY place where:
      - system columns are created
      - system formula dependencies are resolved
    """

    @staticmethod
    @transaction.atomic
    def add_system_column(schema, template_column: SchemaTemplateColumn):
        # -------------------------------------------------
        # 1. Guardrails
        # -------------------------------------------------
        if not template_column.is_system:
            raise ValidationError(
                "Only system template columns may be added via schema expansion."
            )

        if schema.account_type != template_column.template.account_type:
            raise ValidationError(
                "Template column does not belong to this schema's account type."
            )

        # Already exists → no-op
        existing = schema.columns.filter(
            identifier=template_column.identifier
        ).first()
        if existing:
            return existing

        # -------------------------------------------------
        # 2. Resolve formula dependencies FIRST
        # -------------------------------------------------
        if template_column.source == "formula":
            formula = template_column.formula
            if not formula:
                raise ValidationError(
                    f"Template column '{template_column.identifier}' "
                    f"is formula-based but has no formula attached."
                )

            resolver = FormulaDependencyResolver(formula)

            for dep_identifier in resolver.extract_identifiers():
                # Find dependency template
                dep_template = SchemaTemplateColumn.objects.filter(
                    template=template_column.template,
                    identifier=dep_identifier,
                ).first()

                if not dep_template:
                    raise ValidationError(
                        f"System formula '{formula.identifier}' depends on "
                        f"'{dep_identifier}', but no SchemaTemplateColumn exists."
                    )

                # Recursive expansion
                SchemaExpansionService.add_system_column(
                    schema,
                    dep_template,
                )

        # -------------------------------------------------
        # 3. Create the SchemaColumn
        # -------------------------------------------------
        max_order = (
            schema.columns.aggregate_max_order()
            if hasattr(schema.columns, "aggregate_max_order")
            else (
                schema.columns.aggregate(
                    max=models.Max("display_order")
                ).get("max") or 0
            )
        )

        column = SchemaColumn.objects.create(
            schema=schema,
            title=template_column.title,
            identifier=template_column.identifier,
            data_type=template_column.data_type,
            source=template_column.source,
            source_field=(
                None
                if template_column.source == "formula"
                else template_column.source_field
            ),
            formula=template_column.formula,
            is_editable=template_column.is_editable,
            is_deletable=template_column.is_deletable,
            is_system=True,
            display_order=max_order + 1,
        )

        # -------------------------------------------------
        # 4. Create constraints
        # -------------------------------------------------
        SchemaConstraintManager.create_from_master(
            column,
            overrides=template_column.constraints or {},
        )

        # -------------------------------------------------
        # 5. Ensure SCVs exist
        # -------------------------------------------------
        SchemaColumnValueManager.ensure_for_column(column)

        # -------------------------------------------------
        # 6. Recompute centrally
        # -------------------------------------------------
        SCVRefreshService.schema_changed(schema)

        return column
