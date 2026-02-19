from __future__ import annotations

import ast
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

from django.core.exceptions import ValidationError

from formulas.models.formula import Formula


class FormulaEvaluator:
    """
    Safe evaluator for arithmetic formula expressions.

    Supported operations:
    - +, -, *, /, **, unary +/-.
    - Name lookup from provided Decimal context.
    - Numeric constants.
    """

    @staticmethod
    def evaluate(*, formula: Formula, context: Dict[str, Decimal]) -> Decimal:
        try:
            tree = ast.parse(formula.expression, mode="eval")
        except SyntaxError as exc:
            raise ValidationError(
                f"Invalid formula syntax for '{formula.identifier}': {exc}"
            ) from exc

        result = FormulaEvaluator._eval_node(node=tree.body, context=context)

        if formula.decimal_places is not None:
            quantizer = Decimal("1").scaleb(-formula.decimal_places)
            result = result.quantize(quantizer, rounding=ROUND_HALF_UP)

        return result

    @staticmethod
    def _eval_node(*, node, context: Dict[str, Decimal]) -> Decimal:
        if isinstance(node, ast.BinOp):
            left = FormulaEvaluator._eval_node(node=node.left, context=context)
            right = FormulaEvaluator._eval_node(node=node.right, context=context)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ValidationError("Division by zero.")
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
            raise ValidationError(
                f"Unsupported binary operator: {type(node.op).__name__}"
            )

        if isinstance(node, ast.UnaryOp):
            operand = FormulaEvaluator._eval_node(node=node.operand, context=context)
            if isinstance(node.op, ast.UAdd):
                return operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValidationError(
                f"Unsupported unary operator: {type(node.op).__name__}"
            )

        if isinstance(node, ast.Name):
            if node.id not in context:
                raise ValidationError(f"Missing variable '{node.id}' in evaluation context.")
            value = context[node.id]
            try:
                return Decimal(str(value))
            except Exception as exc:
                raise ValidationError(
                    f"Variable '{node.id}' has non-numeric value '{value}'."
                ) from exc

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, Decimal)):
                return Decimal(str(node.value))
            raise ValidationError(
                f"Unsupported constant type: {type(node.value).__name__}"
            )

        raise ValidationError(f"Unsupported expression node: {type(node).__name__}")
