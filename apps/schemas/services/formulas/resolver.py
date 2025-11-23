from decimal import Decimal
from typing import Dict, List
import ast
import logging

from django.core.exceptions import ValidationError

from schemas.models.formula import Formula

logger = logging.getLogger(__name__)


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
    def validate_schema_columns_exist(self, schema):
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
        Build identifier → Decimal mapping with extremely detailed logging.
        """

        logger.debug(
            f"[Resolver] Building context for formula='{self.formula.identifier}' "
            f"holding={holding.id} schema={schema.account_type}"
        )

        from schemas.services.schema_column_value_manager import SchemaColumnValueManager

        self.validate_schema_columns_exist(schema)

        ctx: Dict[str, Decimal] = {}
        deps = self.extract_identifiers()

        logger.debug(f"[Resolver] Dependencies: {deps}")

        for ident in deps:

            column = schema.columns.filter(identifier=ident).first()
            if not column:
                logger.warning(
                    f"[Resolver] Missing column '{ident}', defaulting to 0")
                ctx[ident] = Decimal("0")
                continue

            # SCV manager
            scv_manager = SchemaColumnValueManager.get_or_create(
                holding, column)
            scv = scv_manager.scv

            logger.debug(
                f"[Resolver] Resolving '{ident}' "
                f"(col='{column.title}', type='{column.data_type}', source='{column.source}')"
            )

            # ------------------------------------------------------
            # 1. USER EDITED SCV
            # ------------------------------------------------------
            if scv.is_edited:
                logger.debug(
                    f"[Resolver] '{ident}' -> using user-edited SCV value={scv.value}"
                )
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

                logger.debug(
                    f"[Resolver] '{ident}' -> recursive formula '{column.formula.identifier}'"
                )

                raw_val = FormulaEvaluator.evaluate_for_holding(
                    formula=column.formula,
                    holding=holding,
                    schema=schema,
                    raw=True,
                )

                logger.debug(
                    f"[Resolver] '{ident}' -> formula result={raw_val}")
                ctx[ident] = Decimal(str(raw_val))
                continue

            # ------------------------------------------------------
            # 3. NORMAL COLUMN — display layer SCV
            # ------------------------------------------------------
            try:
                display_val = scv_manager.display_for_column(column, holding)
                logger.debug(
                    f"[Resolver] '{ident}' -> SCV display value={display_val}")
                ctx[ident] = Decimal(str(display_val))
            except Exception as e:
                logger.error(
                    f"[Resolver] FAILED resolving '{ident}': {e}. Falling back to 0."
                )
                ctx[ident] = Decimal("0")

        logger.debug(
            f"[Resolver] Final context for '{self.formula.identifier}': {ctx}")
        return ctx

    # ================================================================
    # CYCLE DETECTION
    # ================================================================
    def detect_cycles(self, schema, start_identifier: str):
        visited = set()
        self._dfs_cycle(schema, start_identifier, visited)

    def _dfs_cycle(self, schema, identifier: str, visited: set):
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
