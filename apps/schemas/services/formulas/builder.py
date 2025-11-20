from django.core.exceptions import ValidationError
from django.db import transaction

from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.formulas.update_engine import FormulaUpdateEngine


class FormulaBuilder:
    """
    AUTO-CREATE MODE FORMULA BUILDER

    Responsibilities:
      ✔ create missing dependency columns as computed columns
      ✔ validate template column integrity
      ✔ detect cycles before attaching formula
      ✔ attach formula to target column
      ✔ ensure SCVs for all holdings
      ✔ evaluate initial SCV values

    Never mutates Holding — only SCVs and SchemaColumns.
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # ============================================================
    # MAIN ENTRYPOINT
    # ============================================================
    @transaction.atomic
    def attach_to_column(self, schema, target_column):
        """
        1. Ensure dependency columns (auto-create missing)
        2. Detect cycles BEFORE saving
        3. Attach formula
        4. Ensure SCVs for all holdings
        5. Compute initial values
        """

        # Lazy import (avoid circular import)
        from schemas.models.schema import SchemaColumn

        resolver = FormulaDependencyResolver(self.formula)

        # ------------------------------------------------------
        # 1. Ensure dependency columns
        # ------------------------------------------------------
        dependency_columns = self._ensure_dependency_columns(schema)

        # ------------------------------------------------------
        # 2. Cycle detection BEFORE commit
        # ------------------------------------------------------
        resolver.detect_cycles(schema, target_column.identifier)

        # ------------------------------------------------------
        # 3. Attach formula to this column
        # ------------------------------------------------------
        target_column.formula = self.formula
        target_column.source = "formula"
        target_column.source_field = None
        target_column.save(update_fields=["formula", "source", "source_field"])

        # ------------------------------------------------------
        # 4. Create SCVs for target + dependency columns
        # ------------------------------------------------------
        self._ensure_scvs(schema, [target_column] + dependency_columns)

        # ------------------------------------------------------
        # 5. Compute initial SCV values
        # ------------------------------------------------------
        self._initial_compute(schema, target_column)

    # ============================================================
    # DEPENDENCY COLUMNS
    # ============================================================
    def _ensure_dependency_columns(self, schema):
        """
        Create missing dependency columns as computed numeric columns.
        Template-defined columns cannot be created.
        """

        from schemas.models.schema import SchemaColumn  # safe import

        resolver = FormulaDependencyResolver(self.formula)
        identifiers = resolver.extract_identifiers()

        template_cols = {
            tc.identifier: tc
            for tc in schema.portfolio.template.columns.all()
        }

        created_or_existing = []

        for ident in identifiers:
            existing = schema.columns.filter(identifier=ident).first()

            if existing:
                created_or_existing.append(existing)
                continue

            # Template-defined column missing → schema corruption
            if ident in template_cols:
                raise ValidationError(
                    f"Formula references '{ident}', a template-defined column "
                    f"missing from schema '{schema.account_type}'. "
                    f"Schema initialization failed."
                )

            # Auto-create computed dependency column
            new_col = SchemaColumn.objects.create(
                schema=schema,
                title=ident.replace("_", " ").title(),
                identifier=ident,
                data_type="decimal",
                source="formula",
                source_field=None,
                is_editable=False,
                is_deletable=True,
                is_system=False,
                display_order=schema.columns.count() + 1,
            )
            created_or_existing.append(new_col)

        return created_or_existing

    # ============================================================
    # SCV CREATION
    # ============================================================
    def _ensure_scvs(self, schema, columns):
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )

        for account in accounts:
            for holding in account.holdings.all():
                for col in columns:
                    SchemaColumnValueManager.get_or_create(holding, col)

    # ============================================================
    # INITIAL COMPUTATION
    # ============================================================
    def _initial_compute(self, schema, target_column):
        """
        Evaluate this formula for every holding using UpdateEngine.
        """
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )

        for account in accounts:
            for holding in account.holdings.all():
                engine = FormulaUpdateEngine(holding, schema)
                engine.update_dependent_formulas(target_column.identifier)
