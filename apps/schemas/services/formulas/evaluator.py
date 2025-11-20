from decimal import Decimal
from typing import Dict
import ast
import operator

from schemas.models.formula import Formula
from schemas.services.formulas.precision import FormulaPrecisionResolver
from schemas.services.formulas.resolver import FormulaDependencyResolver


class FormulaEvaluator:
    """
    Evaluates a formula expression using a SCV-first context.

    - Uses SCV values when present (edited or auto)
    - Uses recursive evaluation for formula columns
    - Applies precision via FormulaPrecisionResolver
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
        """
        Parse and evaluate formula expression.
        """
        expr_ast = ast.parse(self.formula.expression, mode="eval").body
        raw_result = self._eval_ast(expr_ast)
        return self._apply_precision(raw_result)

    # Convenience helper for callers who don’t want to manually resolve precision
    @classmethod
    def evaluate_for_holding(cls, formula: Formula, holding, schema):
        """
        High-level evaluation:
            - Builds SCV context
            - Determines precision
            - Returns formatted Decimal
        """
        ctx = FormulaDependencyResolver(formula).build_context(holding, schema)
        precision = FormulaPrecisionResolver.get_precision(formula)

        evaluator = cls(formula=formula, context=ctx, precision=precision)
        return evaluator.evaluate()

    # ==========================================================
    # AST EVALUATOR
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

        raise ValueError(f"Unsupported AST node: {node!r}")

    # ==========================================================
    # PRECISION
    # ==========================================================
    def _apply_precision(self, value: Decimal) -> Decimal:
        if self.precision is None:
            return value

        quant = Decimal("1").scaleb(-self.precision)  # e.g. precision=2 → 0.01
        return value.quantize(quant)
