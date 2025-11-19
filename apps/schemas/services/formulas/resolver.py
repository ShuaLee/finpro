from decimal import Decimal
from typing import Dict, List
import ast

from django.core.exceptions import ValidationError

from schemas.models.formula import Formula
from schemas.models.schema import SchemaColumn
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class FormulaDependencyResolver:
    """
    READ-ONLY resolver.

    Responsibilities:
      ✔ Extract identifiers from formula expression
      ✔ Validate that referenced schema columns exist
      ✔ Build SCV-first raw evaluation context
      ✔ Support recursive formula evaluation
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # ================================================================
    # IDENTIFIER EXTRACTION
    # ================================================================
    def extract_identifiers(self) -> List[str]:
        tree = ast.parse(self.formula.expression, mode="eval")
        visitor = _IdentifierVisitor()
        visitor.visit(tree)
        return visitor.identifiers

    # ================================================================
    # VALIDATION — NO AUTOCREATION
    # ================================================================
    def validate_schema_columns_exist(self, schema):
        missing = []

        for ident in self.extract_identifiers():
            exists = schema.columns.filter(identifier=ident).exists()
            if not exists:
                missing.append(ident)

        if missing:
            raise ValidationError(
                f"Formula '{self.formula.key}' references missing schema columns: {missing}. "
                f"Add them using FormulaColumnBuilder before evaluating."
            )

    # ================================================================
    # SCV-FIRST CONTEXT BUILDER
    # ================================================================
    def build_context(self, holding, schema) -> Dict[str, Decimal]:
        """
        Build identifier -> Decimal context for formula evaluation.

        Uses this priority:
            1. SCV override (is_edited = True)
            2. SCV auto-display value (computed using schema constraints)
            3. Raw holding/asset fields
            4. Recursive formula output
        """
        self.validate_schema_columns_exist(schema)

        ctx: Dict[str, Decimal] = {}

        for ident in self.extract_identifiers():
            col: SchemaColumn = schema.columns.filter(identifier=ident).first()

            if not col:
                ctx[ident] = Decimal("0")
                continue

            # ----------------------------------------------------------
            # 1. SCV exists?
            # ----------------------------------------------------------
            scv = col.values.filter(holding=holding).first()

            if scv:
                # If user-edited, use SCV raw stored value
                if scv.is_edited:
                    try:
                        ctx[ident] = Decimal(str(scv.value))
                        continue
                    except Exception:
                        ctx[ident] = Decimal("0")
                        continue

                # Not user-edited → use auto display value
                display_value = SchemaColumnValueManager.display_for_column(
                    col, holding
                )
                try:
                    ctx[ident] = Decimal(str(display_value))
                    continue
                except Exception:
                    ctx[ident] = Decimal("0")
                    continue

            # ----------------------------------------------------------
            # 2. FALLBACK: Hold raw value directly
            # ----------------------------------------------------------
            raw = None

            # Holding field
            if col.source == "holding" and col.source_field:
                raw = getattr(holding, col.source_field, None)

            # Asset field
            elif col.source == "asset" and col.source_field:
                asset = holding.asset
                raw = self._resolve_path(
                    asset, col.source_field) if asset else None

            # Recursive formula
            elif col.formula:
                from schemas.services.formulas.evaluator import FormulaEvaluator
                raw = FormulaEvaluator(
                    col.formula, holding, schema).evaluate_raw()

            ctx[ident] = Decimal(str(raw)) if raw is not None else Decimal("0")

        return ctx

    # ================================================================
    # Helper: nested lookup
    # ================================================================
    @staticmethod
    def _resolve_path(obj, path):
        value = obj
        for part in path.split("__"):
            value = getattr(value, part, None)
            if value is None:
                return None
        return value


# ===================================================================
# AST Visitor — Extract identifiers safely
# ===================================================================
class _IdentifierVisitor(ast.NodeVisitor):
    def __init__(self):
        self.identifiers: List[str] = []

    def visit_Name(self, node: ast.Name):
        self.identifiers.append(node.id)
