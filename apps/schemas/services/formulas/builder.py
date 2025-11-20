from django.core.exceptions import ValidationError
from django.db import transaction

from schemas.models.formula import Formula
from schemas.models.schema import Schema, SchemaColumn
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.schema_column_value_manager import SchemaColumnValueManager

from typing import List

import ast


class FormulaBuilder:
    """
    Responsible for attaching a formula to a schema column AND ensuring:

      ✔ All dependencies exist as SchemaColumns
      ✔ Missing ones are created as computed columns
      ✔ Every holding gets SCVs for those columns
      ✔ Initial SCV values are populated

    Absolutely NEVER mutates Holdings.
    SCVs only.
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # =====================================================================
    # MAIN ENTRY POINT
    # =====================================================================
    @transaction.atomic
    def attach_to_column(self, schema: Schema, target_column: SchemaColumn):
        """
        Assign this formula to the target SchemaColumn, build dependencies,
        and populate SCVs.
        """
        # -----------------------------
        # 1. Create or verify dependency columns
        # -----------------------------
        dep_columns = self._ensure_dependency_columns(schema)

        # -----------------------------
        # 2. Attach the formula to target column
        # -----------------------------
        target_column.formula = self.formula
        target_column.source = None
        target_column.source_field = None
        target_column.save(update_fields=["formula", "source", "source_field"])

        # -----------------------------
        # 3. Ensure SCVs exist for all dependency columns + target
        # -----------------------------
        self._ensure_scvs_for_schema(schema, [target_column] + dep_columns)

        # -----------------------------
        # 4. Compute initial SCV values
        # -----------------------------
        self._initial_compute(schema, target_column)

    # =====================================================================
    # DEPENDENCY COLUMN CREATION
    # =====================================================================

    def _ensure_dependency_columns(self, schema: Schema) -> List[SchemaColumn]:
        identifiers = self._extract_identifiers()
        dep_columns = []

        template_columns = {
            tc.identifier: tc
            for tc in schema.portfolio.template.columns.all()
        }

        for ident in identifiers:
            existing = schema.columns.filter(identifier=ident).first()

            if existing:
                dep_columns.append(existing)
                continue

            # 🚫 Prevent duplicating template-defined columns
            if ident in template_columns:
                raise ValidationError(
                    f"Formula references '{ident}', which is a template-defined column "
                    f"but is missing in schema '{schema.account_type}'. "
                    f"This indicates schema initialization failure. "
                    f"Please reinitialize schema instead of creating a custom column."
                )

            # ✔ Safe to create computed column
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

            dep_columns.append(col)

        return dep_columns

    # =====================================================================
    # SCV CREATION
    # =====================================================================
    def _ensure_scvs_for_schema(self, schema: Schema, columns: List[SchemaColumn]):
        """
        Ensure SCVs exist for all holdings for all columns.
        """
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type)

        for account in accounts:
            for holding in account.holdings.all():
                for col in columns:
                    SchemaColumnValueManager.get_or_create(holding, col)

    # =====================================================================
    # INITIAL COMPUTATION
    # =====================================================================
    def _initial_compute(self, schema: Schema, target_col: SchemaColumn):
        """
        After attaching a formula, compute its value for all holdings and
        store the result in SCVs.
        """
        resolver = FormulaDependencyResolver()

        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type)

        for account in accounts:
            for holding in account.holdings.all():
                scv = SchemaColumnValueManager.get_or_create(
                    holding, target_col).scv

                result = resolver.evaluate(
                    formula=self.formula, holding=holding, schema=schema)

                scv.value = str(result)
                scv.is_edited = False
                scv.save(update_fields=["value", "is_edited"])

    # =====================================================================
    # HELPER — IDENTIFIER EXTRACTION
    # =====================================================================
    def _extract_identifiers(self) -> List[str]:
        """
        Parse formula.expression and return identifiers (variable names).
        """
        tree = ast.parse(self.formula.expression, mode="eval")
        visitor = _IdentifierVisitor()
        visitor.visit(tree)
        return visitor.identifiers

# =====================================================================
# Visitor to extract names from formula expressions
# =====================================================================


class _IdentifierVisitor(ast.NodeVisitor):
    def __init__(self):
        self.identifiers: List[str] = []

    def visit_Name(self, node):
        self.identifiers.append(node.id)
