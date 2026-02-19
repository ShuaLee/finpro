from typing import Iterable, Set, Dict, Any

from formulas.models.formula import Formula


class DependencyInspector:
    """
    Introspection utilities for Formula dependencies.

    Used by:
    - schema expansion logic
    - UI previews
    - validation checks
    - analytics preflight

    This class does NOT:
    - mutate schemas
    - evaluate formulas
    - access the database
    """

    @staticmethod
    def required_identifiers(*, formula: Formula) -> Set[str]:
        """
        Return the identifiers required by the formula.
        """
        return set(formula.dependencies)

    @staticmethod
    def missing_identifiers(
        *,
        formula: Formula,
        available_identifiers: Iterable[str],
    ) -> Set[str]:
        """
        Return identifiers required by the formula that are missing
        from the available identifiers.
        """
        required = set(formula.dependencies)
        available = set(available_identifiers)

        return required - available

    @staticmethod
    def can_resolve(
        *,
        formula: Formula,
        available_identifiers: Iterable[str],
    ) -> bool:
        """
        Return True if all required identifiers are available.
        """

        return not DependencyInspector.missing_identifiers(
            formula=formula,
            available_identifiers=available_identifiers
        )

    @staticmethod
    def inspect(
        *,
        formula: Formula,
        available_identifiers: Iterable,
    ) -> Dict[str, Any]:
        """
        Return a structured inspection report.

        Useful for UI and debugging.
        """

        required = set(formula.dependencies)
        available = set(available_identifiers)

        missing = required - available
        extra = available - required

        return {
            "formula": formula.identifier,
            "required": sorted(required),
            "available": sorted(available),
            "missing": sorted(missing),
            "extra": sorted(extra),
            "is_resolvable": not missing,
        }
