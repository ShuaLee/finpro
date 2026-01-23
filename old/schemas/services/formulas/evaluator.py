from decimal import Decimal, DivisionByZero, InvalidOperation
from typing import Dict
import ast
import operator

from schemas.models.formula import Formula
from schemas.services.formulas.precision import FormulaPrecisionResolver

import logging

logger = logging.getLogger(__name__)


class FormulaEvaluator:
    """
    Safely evaluates formula expressions using a precomputed SCV-first context.

    Public API:
        evaluate_raw()               → Decimal (no rounding)
        evaluate()                   → Decimal (with precision)
        evaluate_for_holding(...)    → shortcut entrypoint
    """

    # Allowed operators
    SAFE_BINARY = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    SAFE_UNARY = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def __init__(self, formula: Formula, context: Dict[str, Decimal], precision: int):
        self.formula = formula
        self.context = context
        self.precision = precision

    # ==================================================================
    # PUBLIC — RAW EVALUATION
    # ==================================================================
    def evaluate_raw(self) -> Decimal:
        """
        Evaluate without rounding — used when other formulas depend on this one.
        """
        expr_ast = ast.parse(self.formula.expression, mode="eval").body

        logger.debug(
            f"[FormulaEvaluator] RAW eval for {self.formula.identifier} "
            f"with context={self.context}"
        )
        return self._eval_ast(expr_ast)

    # ==================================================================
    # PUBLIC — FORMATTED EVALUATION
    # ==================================================================
    def evaluate(self) -> Decimal:
        """
        Evaluate and apply decimal precision rules.
        """
        raw = self.evaluate_raw()

        logger.debug(
            f"[FormulaEvaluator] FORMATTED eval for {self.formula.identifier} "
            f"precision={self.precision}"
        )

        return self._apply_precision(raw)

    # ==================================================================
    # PUBLIC — HIGH LEVEL SHORTCUT
    # ==================================================================
    @classmethod
    def evaluate_for_holding(cls, formula: Formula, holding, schema, raw=False):
        from schemas.services.formulas.resolver import FormulaDependencyResolver
        """
        Fast shortcut:

            - Build SCV-first context
            - Determine precision
            - Evaluate raw or formatted
        """
        resolver = FormulaDependencyResolver(formula)
        context = resolver.build_context(holding, schema)

        precision = FormulaPrecisionResolver.get_precision(
            formula=formula,
            target_column=None,
        )

        evaluator = cls(
            formula=formula,
            context=context,
            precision=precision,
        )

        if raw:
            return evaluator.evaluate_raw()

        return evaluator.evaluate()

    # ==================================================================
    # INTERNAL — AST WALKER
    # ==================================================================
    def _eval_ast(self, node):
        """
        Recursive safe evaluation of an AST node.
        """

        # --- binary operators (a + b, a - b, a * b, etc.) ---
        if isinstance(node, ast.BinOp):
            left = self._eval_ast(node.left)
            right = self._eval_ast(node.right)

            op = self.SAFE_BINARY.get(type(node.op))
            if not op:
                raise ValueError(
                    f"Unsupported operator: {type(node.op).__name__}")

            try:
                return op(left, right)
            except DivisionByZero:
                return Decimal("0")
            except InvalidOperation:
                return Decimal("0")

        # --- unary operators (-x, +x) ---
        if isinstance(node, ast.UnaryOp):
            op = self.SAFE_UNARY.get(type(node.op))
            if not op:
                raise ValueError(
                    f"Unsupported unary operator: {type(node.op).__name__}")
            operand = self._eval_ast(node.operand)
            return op(operand)

        # --- numeric constants ---
        if isinstance(node, ast.Constant):
            value = node.value

            # Allow only numeric literals
            if isinstance(value, (int, float, Decimal)):
                try:
                    return Decimal(str(value))
                except (InvalidOperation, ValueError):
                    raise ValueError(
                        f"Invalid numeric constant '{value}' "
                        f"in formula '{self.formula.identifier}'"
                    )

            raise ValueError(
                f"Unsupported constant '{value}' "
                f"(type {type(value).__name__}) "
                f"in formula '{self.formula.identifier}'"
            )


        # --- variable reference ---
        if isinstance(node, ast.Name):
            if node.id not in self.context:
                raise ValueError(f"Missing SCV context for '{node.id}' in formula '{self.formula.identifier}'")
            return self.context[node.id]


        # --- Anything else is disallowed ---
        raise ValueError(f"Unsupported expression element: {ast.dump(node)}")

    # ==================================================================
    # INTERNAL — PRECISION
    # ==================================================================
    def _apply_precision(self, value: Decimal) -> Decimal:
        if self.precision is None:
            return value

        quant = Decimal("1").scaleb(-self.precision)  # 2 → 0.01
        try:
            return value.quantize(quant)
        except InvalidOperation:
            return value
