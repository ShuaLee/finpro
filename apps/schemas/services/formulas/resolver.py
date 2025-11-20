from decimal import Decimal
from typing import Dict, List
import ast

from django.core.exceptions import ValidationError

from schemas.models.formula import Formula
from schemas.models.schema import Schema, SchemaColumn
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class FormulaDependencyResolver:
    """
    READ-ONLY resolver.

    Responsibilities:
      ✔ Extract identifiers from the formula expression
      ✔ Validate referenced schema columns exist
      ✔ Build SCV-first Decimal context
      ✔ Recursively evaluate formula columns
      ✔ Detect cycles
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # ================================================================
    # IDENTIFIER EXTRACTION
    # ================================================================
    def extract_identifiers(self) -> List[str]:
        """Parse AST & return identifiers."""
        tree = ast.parse(self.formula.expression, mode="eval")
        visitor = _IdentifierVisitor()
        visitor.visit(tree)
        return visitor.identifiers

    # ================================================================
    # VALIDATION — NO AUTOCREATION
    # ================================================================
    def validate_schema_columns_exist(self, schema: Schema):
        missing = []
        for ident in self.extract_identifiers():
            if not schema.columns.filter(identifier=ident).exists():
                missing.append(ident)

        if missing:
            raise ValidationError(
                f"Formula '{self.formula.key}' references missing columns: {missing}. "
                "These must exist before attaching a formula."
            )

    # ================================================================
    # SCV-FIRST CONTEXT
    # ================================================================
    def build_context(self, holding, schema) -> Dict[str, Decimal]:
        """
        Build identifier → Decimal mapping:

            1. SCV.value (edited)
            2. SCV display-layer (auto-calculated)
            3. Recursive formula evaluation
            4. Default = 0
        """
        self.validate_schema_columns_exist(schema)

        ctx: Dict[str, Decimal] = {}

        for ident in self.extract_identifiers():

            column = schema.columns.filter(identifier=ident).first()
            if not column:
                ctx[ident] = Decimal("0")
                continue

            scv_manager = SchemaColumnValueManager.get_or_create(
                holding, column)
            scv = scv_manager.scv

            # ------------------------------------------------------
            # 1. USER EDITED SCV
            # ------------------------------------------------------
            if scv.is_edited:
                try:
                    ctx[ident] = Decimal(str(scv.value))
                except:
                    ctx[ident] = Decimal("0")
                continue

            # ------------------------------------------------------
            # 2. FORMULA COLUMN (recursive)
            # ------------------------------------------------------
            if column.formula:
                from schemas.services.formulas.evaluator import FormulaEvaluator

                raw_val = FormulaEvaluator.evaluate_for_holding(
                    formula=column.formula,
                    holding=holding,
                    schema=schema,
                    raw=True,  # raw = no precision formatting here
                )

                ctx[ident] = Decimal(str(raw_val))
                continue

            # ------------------------------------------------------
            # 3. NORMAL COLUMN — display value
            # ------------------------------------------------------
            display_val = scv_manager.display_for_column(column, holding)
            try:
                ctx[ident] = Decimal(str(display_val))
            except:
                ctx[ident] = Decimal("0")

        return ctx

    # ================================================================
    # CYCLE DETECTION
    # ================================================================
    def detect_cycles(self, schema: Schema, start_identifier: str):
        visited = set()
        self._dfs_cycle(schema, start_identifier, visited)

    def _dfs_cycle(self, schema: Schema, identifier: str, visited: set):
        if identifier in visited:
            raise ValidationError(
                f"Formula dependency cycle detected involving '{identifier}'."
            )

        visited.add(identifier)

        col = schema.columns.filter(identifier=identifier).first()
        if not col or not col.formula:
            return

        deps = self.extract_identifiers()
        for dep in deps:
            self._dfs_cycle(schema, dep, visited.copy())


# ===================================================================
# Identifier Visitor
# ===================================================================

class _IdentifierVisitor(ast.NodeVisitor):
    def __init__(self):
        self.identifiers: List[str] = []

    def visit_Name(self, node: ast.Name):
        self.identifiers.append(node.id)
