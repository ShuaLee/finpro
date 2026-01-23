from decimal import Decimal, getcontext, ROUND_HALF_UP
from typing import Dict

from django.core.exceptions import ValidationError

from formulas.models.formula import Formula


class FormulaEvaluator:
    """
    Executes a Formula against a prepared evaluation context.

    Assumes:
    - Dependencies have already been resolved
    - Context values are Decimals
    """

    @staticmethod
    def evaluate(*, formula: Formula, context: Dict[str, Decimal]) -> Decimal:
        """
        Evaluate a formula using a resolved context.

        Args:
            formula: Formula to evaluate
            context: Mapping of identifier -> Decimal value

        Returns:
            Decimal result

        Raises:
            ValidationError if evaluation fails
        """

        try:
            # Evaluate expression in a tightly controlled namespace
            result = eval(
                compile(formula.expression, "<formula>", "eval"),
                {"__builtins__": {}},
                context,
            )
        except Exception as exc:
            raise ValidationError(
                f"Error evaluating formula '{formula.identifier}': {exc}"
            )

        if not isinstance(result, (int, float, Decimal)):
            raise ValidationError(
                f"Formula '{formula.identifier}' did not return a numeric value."
            )

        result = Decimal(result)

        # Apply precision if specified
        if formula.decimal_places is not None:
            quantizer = Decimal("1").scaleb(-formula.decimal_places)
            result = result.quantize(
                quantizer,
                rounding=ROUND_HALF_UP,
            )

        return result
