from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

import ast
import operator


class FormulaEvaluator:
    """
    Evaluates formulas safely using:
      - SCV values (preferred)
      - Raw backend values only if SCV missing
      - Recursive formula evaluation for formula-based columns

    Precision rules:
      - system formulas → constraints
      - user formulas → formula.decimal_places
    """

    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def __init__(self, formula: Formula, context: Dict[str, Decimal], precision: int):
        self.formula = formula
        self.context = context
        self.precision = precision

    # ==========================================================
    # PUBLIC API
    # ==========================================================
    def evaluate(self) -> Decimal:
        expr_ast = ast.parse(self.formula.expression, mode="eval").body
        raw_result = self._eval_ast(expr_ast)
        return self._apply_precision(raw_result)

    # ==========================================================
    # AST WALKER
    # ==========================================================
    def _eval_ast(self, node):
        if isinstance(node, ast.BinOp):
            left = self._eval_ast(node.left)
            right = self._eval_ast(node.right)
            op = self.SAFE_OPERATORS[type(node.op)]
            return op(left, right)

        elif isinstance(node, ast.Constant):
            return Decimal(str(node.value))

        elif isinstance(node, ast.Name):
            return self.context.get(node.id, Decimal("0"))

        else:
            raise ValueError(f"Unsupported AST node: {node}")

    # ==========================================================
    # PRECISION RULES
    # ==========================================================
    def _apply_precision(self, value: Decimal) -> Decimal:
        if self.precision is None:
            # Fallback safety net
            return value

        quant = Decimal("1").scaleb(-self.precision)
        return value.quantize(quant)
