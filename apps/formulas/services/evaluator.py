from formulas.services.precision import apply_precision
from decimal import Decimal
import ast
import operator


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
        values: dict mapping identifier -> Decimal (e.g., {"quantity": Decimal("5"), "price": Decimal("100.25")})
        constraints: column constraints (like {"decimal_places": 2})
        """
        self.formula = formula
        self.values = values
        self.constraints = constraints or {}

    def eval(self) -> Decimal:
        expr_ast = ast.parse(self.formula.expression, mode="eval").body
        result = self._eval_ast(expr_ast)
        return apply_precision(result, list(self.values.values()), self.constraints)

    def _eval_ast(self, node):
        if isinstance(node, ast.BinOp):
            left = self._eval_ast(node.left)
            right = self._eval_ast(node.right)
            op = self.SAFE_OPERATORS[type(node.op)]
            return op(left, right)
        elif isinstance(node, ast.Num):
            return Decimal(str(node.n))
        elif isinstance(node, ast.Name):
            return self.values.get(node.id, Decimal("0"))
        else:
            raise ValueError(f"Unsupported AST node: {node}")
