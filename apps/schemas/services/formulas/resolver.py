from decimal import Decimal
from typing import Dict, List
import ast

from django.core.exceptions import ValidationError

from schemas.models.formula import Formula
from schemas.models.schema import Schema, SchemaColumn
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class FormulaDependencyResolver:
    """
    READ-ONLY dependency resolver.

    Responsibilities:
      ✔ Extract identifiers from formula expression
      ✔ Ensure referenced schema columns already exist
      ✔ Build a Decimal context using the SCV layer (not raw holding values)
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # ================================================================
    # IDENTIFIER EXTRACTION
    # ================================================================
    def extract_identifiers(self) -> List[str]:
        """
        Parse AST and extract any variable names used in the expression.
        """
        tree = ast.parse(self.formula.expression, mode="eval")
        visitor = _IdentifierVisitor()
        visitor.visit(tree)
        return visitor.visit(tree)

    # ================================================================
    # VALIDATION — NO AUTOCREATION
    # ================================================================
    def validate_schema_columns_exist(self, schema: Schema):
        """
        Ensure all identifiers used in formula are real schema columns.
        If any are missing → formula cannot be evaluated.
        """
        missing = []

        for ident in self.extract_identifiers():
            if not schema.columns.filter(identifier=ident).exists():
                missing.append(ident)

        if missing:
            raise ValidationError(
                f"Formula '{self.formula.key}' references missing schema columns: "
                f"{missing}. Columns must be created first."
            )

    # ================================================================
    # SCV-FIRST CONTEXT BUILDER
    # ================================================================
    def build_context(self, holding, schema) -> Dict[str, Decimal]:
        """
        Build identifier → Decimal mapping using SCVs:

        Priority:
            1. SCV.value if edited
            2. SCV.refresh_display from raw holding/asset
            3. If formula column, evaluate recursively
            4. Else 0
        """
        self.validate_schema_columns_exist(schema)

        context: Dict[str, Decimal] = {}

        for ident in self.extract_identifiers():
            column: SchemaColumn = schema.columns.filter(
                identifier=ident
            ).first()

            if not column:
                context[ident] = Decimal("0")
                continue

            scv_manager = SchemaColumnValueManager.get_or_create(
                holding, column)
            scv = scv_manager.scv

            # ---------------------------------------------
            # 1. USER-EDITED SCV OVERRIDES EVERYTHING
            # ---------------------------------------------
            if scv.is_edited:
                try:
                    context[ident] = Decimal(str(scv.value))
                except:
                    context[ident] = Decimal("0")
                continue

            # ---------------------------------------------
            # 2. RECURSIVE FORMULA COLUMN
            # ---------------------------------------------
            if column.formula:
                from schemas.services.formulas.evaluator import FormulaEvaluator
                value = FormulaEvaluator(
                    column.formula, holding, schema).evaluate_raw()
                context[ident] = Decimal(str(value))
                continue

            # ---------------------------------------------
            # 3. NORMAL BACKEND-DERIVED SCV (raw → display)
            # ---------------------------------------------
            display_val = scv_manager.display_for_column(column, holding)

            try:
                context[ident] = Decimal(str(display_val))
            except:
                context[ident] = Decimal("0")

        return context


# ===================================================================
# AST Visitor — Extract identifiers safely
# ===================================================================
class _IdentifierVisitor(ast.NodeVisitor):
    def __init__(self):
        self.identifiers: List[str] = []

    def visit_Name(self, node: ast.Name):
        """
        Called for every identifier in the expression.
        Example: price * quantity → ["price", "quantity"]
        """
        self.identifiers.append(node.id)
