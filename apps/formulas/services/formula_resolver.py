from decimal import Decimal
from typing import Dict, Any

from django.core.exceptions import ValidationError

from formulas.models.formula import Formula

import ast


class FormulaResolver:
    """
    Prepares an evaluation context for a Formula.

    Responsibilities:
    - Verify required dependencies exist
    - Normalize numeric inputs
    - Produce a safe context for evaluation

    This class does NOT:
    - evaluate formulas
    - mutate schemas
    - access the database
    """

    IMPLICIT_IDENTIFIERS = {
        "fx_rate",
    }

    @classmethod
    def is_implicit(cls, identifier: str) -> bool:
        return identifier in cls.IMPLICIT_IDENTIFIERS

    @staticmethod
    def resolve_inputs(
        *,
        formula: Formula,
        context: Dict[str, Any],
        allow_missing: bool = False,
        default_missing: Decimal | int | float | None = None,
    ) -> Dict[str, Decimal]:
        """
        Resolve and normalize inputs for a formula.

        Args:
            formula: Formula being evaluated
            context: Mapping of identifier -> value
            allow_missing: If True, missing dependencies are filled with default_missing
            default_missing: Value to use for missing dependencies

        Returns:
            Normalized context suitable for evaluation

        Raises:
            ValidationError if required dependencies are missing or invalid
        """

        resolved: Dict[str, Decimal] = {}

        for identifier in formula.dependencies:
            if identifier not in context:
                if not allow_missing:
                    raise ValidationError(
                        f"Missing required dependency '{identifier}' "
                        f"for formula '{formula.identifier}'."
                    )

                resolved[identifier] = Decimal(default_missing or 0)
                continue

            value = context[identifier]

            if value is None:
                if not allow_missing:
                    raise ValidationError(
                        f"Dependency '{identifier}' is None "
                        f"for formula '{formula.identifier}'."
                    )

                resolved[identifier] = Decimal(default_missing or 0)
                continue

            try:
                resolved[identifier] = Decimal(value)
            except Exception:
                raise ValidationError(
                    f"Invalid value for dependency '{identifier}': {value}"
                )

        return resolved

    @staticmethod
    def required_identifiers(formula):
        """
        Return a set of variable identifiers required by this formula.
        Example: "quantity * price" -> {"quantity", "price"}
        """

        tree = ast.parse(formula.expression, mode="eval")

        identifiers = set()

        class Visitor(ast.NodeVisitor):
            def visit_Name(self, node):
                identifiers.add(node.id)

        Visitor().visit(tree)

        return identifiers
