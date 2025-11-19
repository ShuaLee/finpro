from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver

from decimal import Decimal, ROUND_HALF_UP

import ast
import operator


class FormulaEvaluator:
    """
    Evaluates formula expressions using BEDMAS-safe AST parsing.

    Supports:
      - Raw value evaluation (no rounding)
      - Formatted evaluation (decimal_places applied)
      - Recursive formulas
    """

    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv
    }

    def __init__(self, formula: Formula, holding, schema):
        self.formula = formula
        self.holding = holding
        self.schema = schema

        self.resolver = FormulaDependencyResolver(formula)

    # =====================================================================
    # PUBLIC: RAW & FORMATTED EVALUATION
    # =====================================================================
    def evaluate_raw(self) -> Decimal:
        """
        Evaluate the numeric expression WITHOUT applying any rounding
        """
        values = self.resolver.build_raw_context(self.holding, self.schema)
        expr_ast = ast.parse(self.formula.expression, mode="eval").body
        return self._eval_ast(expr_ast, values)

    def evaluate_formatted(self) -> Decimal:
        """
        Evaluate formula and apply decimal_places rules for display.
        """
        raw = self.evaluate_raw()
        places = self._resolve_decimal_places()
        return self._apply_precision(raw, places)

    # =====================================================================
    # AST EVALUATION
    # =====================================================================
    def _eval_ast(self, node, values: dict) -> Decimal:
        """
        Recursively evaluate AST nodes to compute Decimal result.
        """
        # Binary operators: +, -, *, /
        if isinstance(node, ast.BinOp):
            left = self._eval_ast(node.left, values)
            right = self._eval_ast(node.right, values)

            op_class = type(node.op)
            if op_class not in self.SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {op_class.__name__}")

            return self.SAFE_OPERATORS[op_class](left, right)

        # Literal constant
        elif isinstance(node, ast.Constant):
            return Decimal(str(node.value))

        # Variable reference (identifier)
        elif isinstance(node, ast.Name):
            return values.get(node.id, Decimal("0"))

        raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    # =====================================================================
    # DECIMAL PLACES RESOLUTION
    # =====================================================================
    def _resolve_decimal_places(self) -> int:
        """
        Rules:
          1. If formula.decimal_places is set -> use that
          2. Else if system formula -> fallback to 2 decimals
          3. Else (user formula, no precision) -> default to 2
        """
        if self.formula.decimal_places is not None:
            return self.formula.decimal_places

        # system formulas fallback to 2
        if self.formula.is_system:
            return 2

        # custom formulas also default to 2
        return 2

    # =====================================================================
    # PRECISION APPLY
    # =====================================================================
    @staticmethod
    def _apply_precision(value: Decimal, places: int) -> Decimal:
        """
        Round to given decimal places using ROUND_HALF_UP.
        """
        if places <= 0:
            return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        quant = Decimal("1").scaleb(-places)
        return value.quantize(quant, rounding=ROUND_HALF_UP)
