import operator
import ast
from decimal import Decimal
from formulas.services.precision import apply_precision


class FormulaEvaluator:
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def __init__(self, formula, values: dict, constraints: dict = None):
        """
        formula: Formula object
        values: dict mapping identifiers -> Decimal values
        constraints: optional dict, e.g. from SchemaColumnTemplate (system formulas)
        """
        self.formula = formula
        self.values = values
        self.constraints = constraints or {}

    def eval(self) -> Decimal:
        expr_ast = ast.parse(self.formula.expression, mode="eval").body
        result = self._eval_ast(expr_ast)

        # System formulas -> constraints decide precision
        # User formulas -> formula.decimal_places must be set
        return apply_precision(
            result,
            self.formula,
            self.constraints
        )

    def _eval_ast(self, node):
        if isinstance(node, ast.BinOp):
            left = self._eval_ast(node.left)
            right = self._eval_ast(node.right)
            op = self.SAFE_OPERATORS[type(node.op)]
            return op(left, right)

        elif isinstance(node, ast.Constant):  # Python 3.8+
            return Decimal(str(node.value))

        elif isinstance(node, ast.Name):
            return self.values.get(node.id, Decimal("0"))

        else:
            raise ValueError(f"Unsupported AST node: {node}")
