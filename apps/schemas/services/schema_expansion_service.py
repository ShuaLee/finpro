from django.core.exceptions import ValidationError
from django.db import transaction, models

from schemas.models.schema_column import SchemaColumn
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_asset_behaviour import SchemaColumnAssetBehaviour
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from schemas.services.schema_column_value_manager import SchemaColumnValueManager

from formulas.services.formula_resolver import FormulaResolver


class SchemaExpansionService:
    """
    Expands a Schema by adding SYSTEM columns and their dependencies.

    Asset-type-aware.
    Structural only.
    Deterministic.
    """

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================
    @staticmethod
    @transaction.atomic
    def add_system_column(schema, template_column: SchemaColumnTemplate):
        """
        Ensure a system SchemaColumn (and its dependencies) exists.
        """
        from schemas.services.scv_refresh_service import SCVRefreshService

        if not template_column.is_system:
            raise ValidationError(
                "Only system template columns may be expanded."
            )

        # --------------------------------------------------
        # 1. Already exists → no-op
        # --------------------------------------------------
        existing = schema.columns.filter(
            identifier=template_column.identifier
        ).first()

        if existing:
            return existing

        # --------------------------------------------------
        # 2. Resolve dependencies PER ASSET TYPE
        # --------------------------------------------------
        for t_behavior in template_column.behaviours.select_related(
            "asset_type",
            "formula_definition",
        ):
            if t_behavior.source != "formula":
                continue

            definition = t_behavior.formula_definition
            if not definition:
                raise ValidationError(
                    f"Template column '{template_column.identifier}' "
                    f"has formula behavior without FormulaDefinition "
                    f"for asset type '{t_behavior.asset_type.slug}'."
                )

            formula = definition.formula

            for dep_identifier in FormulaResolver.required_identifiers(formula):

                # --------------------------------------------------
                # Skip implicit runtime identifiers (e.g. fx_rate)
                # --------------------------------------------------
                if FormulaResolver.is_implicit(dep_identifier):
                    continue

                dep_template = SchemaColumnTemplate.objects.filter(
                    identifier=dep_identifier,
                    is_system=True,
                ).first()

                if not dep_template:
                    raise ValidationError(
                        f"System formula '{formula.identifier}' "
                        f"depends on '{dep_identifier}', but no system "
                        f"SchemaColumnTemplate exists."
                    )

                SchemaExpansionService.add_system_column(
                    schema=schema,
                    template_column=dep_template,
                )

        # --------------------------------------------------
        # 3. Create SchemaColumn
        # --------------------------------------------------
        max_order = (
            schema.columns.aggregate(
                max=models.Max("display_order")
            ).get("max") or 0
        )

        column = SchemaColumn.objects.create(
            schema=schema,
            identifier=template_column.identifier,
            title=template_column.title,
            data_type=template_column.data_type,
            template=template_column,
            is_system=True,
            is_editable=False,
            is_deletable=False,
            display_order=max_order + 1,
        )

        # --------------------------------------------------
        # 4. Copy TEMPLATE BEHAVIORS → SCHEMA BEHAVIORS
        # --------------------------------------------------
        for t_behavior in template_column.behaviours.all():
            SchemaColumnAssetBehaviour.objects.create(
                column=column,
                asset_type=t_behavior.asset_type,
                source=t_behavior.source,
                formula_definition=t_behavior.formula_definition,
                source_field=t_behavior.source_field,
                constant_value=t_behavior.constant_value,
                is_override=False,
            )

        # --------------------------------------------------
        # 5. Attach constraints
        # --------------------------------------------------
        SchemaConstraintManager.create_from_master(
            column,
            overrides=getattr(template_column, "constraints", None) or {},
        )

        # --------------------------------------------------
        # 6. Ensure SCVs exist (NO recompute)
        # --------------------------------------------------
        SchemaColumnValueManager.ensure_for_column(column)

        # --------------------------------------------------
        # 7. Single recompute
        # --------------------------------------------------
        SCVRefreshService.schema_changed(schema)

        return column
