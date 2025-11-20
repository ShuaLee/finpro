from django.core.exceptions import ValidationError
from django.db import transaction

from schemas.models.formula import Formula
from schemas.models.schema import Schema, SchemaColumn
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.formulas.update_engine import FormulaUpdateEngine

import ast


class FormulaBuilder:
    """
    Responsible for attaching a formula to a SchemaColumn AND ensuring:

      ✔ All dependency identifiers already exist (template OR custom)
      ✔ Missing dependencies become computed columns
      ✔ SCVs created for all holdings
      ✔ Initial SCV values evaluated using SCV-first logic
      ✔ Cycle detection before attach

    *Never* mutates Holdings — only SCVs & SchemaColumns.
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # ============================================================
    # MAIN ENTRYPOINT
    # ============================================================
    @transaction.atomic
    def attach_to_column(self, schema: Schema, target_column: SchemaColumn):
        """
        Attach the formula to the target schema column.
        Create missing dependency columns (computed only).
        Seed SCVs.
        Evaluate initial values.
        """

        resolver = FormulaDependencyResolver(self.formula)

        # -------------------------------------------------------
        # 1. Create or reuse dependency columns
        # -------------------------------------------------------
        dependency_columns = self._ensure_dependency_columns(schema)

        # -------------------------------------------------------
        # 2. Detect circular reference BEFORE committing
        # -------------------------------------------------------
        resolver.detect_cycles(schema, target_column.identifier)

        # -------------------------------------------------------
        # 3. Attach formula to the schema column
        # -------------------------------------------------------
        target_column.formula = self.formula
        target_column.source = "formula"
        target_column.source_field = None
        target_column.save(update_fields=["formula", "source", "source_field"])

        # -------------------------------------------------------
        # 4. SCVs for target + dependency columns
        # -------------------------------------------------------
        self._ensure_scvs(schema, [target_column] + dependency_columns)

        # -------------------------------------------------------
        # 5. Initial computation (populate SCVs)
        # -------------------------------------------------------
        self._initial_compute(schema, target_column)

    # ============================================================
    # DEPENDENCY COLUMNS
    # ============================================================
    def _ensure_dependency_columns(self, schema: Schema):
        """
        Ensures that identifiers referenced in the formula exist as SchemaColumns.
        Missing ones are auto-created as computed formula columns.

        NOTE:
            Template columns can **never** be auto-created.
        """
        resolver = FormulaDependencyResolver(self.formula)
        identifiers = resolver.extract_identifiers()

        # Look up portfolio template
        template_cols = {
            tc.identifier: tc
            for tc in schema.portfolio.template.columns.all()
        }

        created_or_existing = []

        for ident in identifiers:

            # Already present?
            col = schema.columns.filter(identifier=ident).first()
            if col:
                created_or_existing.append(col)
                continue

            # A template-defined column missing in schema? → schema corruption
            if ident in template_cols:
                raise ValidationError(
                    f"Formula references '{ident}', which is defined in the template "
                    f"but missing from schema '{schema.account_type}'. "
                    f"This indicates schema initialization failure."
                )

            # SAFE computed column
            col = SchemaColumn.objects.create(
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

            created_or_existing.append(col)

        return created_or_existing

    # ============================================================
    # SCV CREATION
    # ============================================================
    def _ensure_scvs(self, schema: Schema, columns):
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
    def _initial_compute(self, schema: Schema, target_column: SchemaColumn):
        """
        Recompute the formula for every holding — using SCV-first logic.
        """
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )

        for account in accounts:
            for holding in account.holdings.all():
                engine = FormulaUpdateEngine(holding, schema)
                engine.update_dependent_formulas(target_column.identifier)


# ============================================================
# HELPER — Extract identifiers
# ============================================================

class _IdentifierVisitor(ast.NodeVisitor):
    def __init__(self):
        self.identifiers = []

    def visit_Name(self, node):
        self.identifiers.append(node.id)
