from typing import List, Set

from schemas.services.formulas.resolver import FormulaDependencyResolver


class FormulaUpdateEngine:
    """
    Dependency traversal engine for formula columns.

    Responsibilities:
        - Determine which formula columns depend on a changed identifier
        - Traverse dependency graph safely
        - Return ordered list of columns to recompute

    NON-responsibilities:
        ❌ Recompute values
        ❌ Write SchemaColumnValues
        ❌ Apply precision
        ❌ Decide recompute rules

    Actual recomputation is handled by:
        → SchemaManager
    """

    def __init__(self, schema):
        self.schema = schema

    # ============================================================
    # PUBLIC API
    # ============================================================
    def get_dependent_formula_columns(
        self,
        changed_identifier: str,
    ) -> List:
        """
        Return all formula SchemaColumns that depend (directly or indirectly)
        on the given identifier.

        Order is safe for recomputation.
        """
        visited: Set[str] = set()
        ordered = []

        self._dfs(changed_identifier, visited, ordered)
        return ordered

    # ============================================================
    # DEPTH-FIRST TRAVERSAL
    # ============================================================
    def _dfs(self, identifier: str, visited: Set[str], ordered: list):
        for column in self._formula_columns_depending_on(identifier):
            if column.identifier in visited:
                continue

            visited.add(column.identifier)

            # Recurse first (topological-ish order)
            self._dfs(column.identifier, visited, ordered)

            ordered.append(column)

    # ============================================================
    # DEPENDENCY LOOKUP
    # ============================================================
    def _formula_columns_depending_on(self, identifier: str):
        """
        Find formula columns whose formula references `identifier`.
        """
        for column in self.schema.columns.filter(source="formula"):
            if not column.formula:
                continue

            resolver = FormulaDependencyResolver(column.formula)
            if identifier in resolver.extract_identifiers():
                yield column
