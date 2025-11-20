from schemas.models.schema import Schema, SchemaColumnValue
from schemas.services.formulas.evaluator import FormulaEvaluator
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.formulas.precision import FormulaPrecisionResolver


class FormulaUpdateEngine:
    """
    Recalculates ALL formula-based column values for a single holding whenever:

        - a user edits an SCV
        - a backend holding value changes
        - a dependent formula changes

    Features:
        ✔ SCV-first evaluation
        ✔ Cycle-safe dependency graph traversal
        ✔ Chained formula propagation
        ✔ Precision from constraints or formula settings
    """

    def __init__(self, holding, schema: Schema):
        self.holding = holding
        self.schema = schema

    # ============================================================
    # PUBLIC ENTRYPOINT
    # ============================================================
    def update_dependent_formulas(self, changed_identifier: str):
        """
        Trigger a recalculation of *all* formulas that depend on a column
        identified by `changed_identifier`.

        Automatically handles chained dependencies via DFS.
        """
        visited = set()
        self._recompute_recursive(changed_identifier, visited)

    # ============================================================
    # INTERNAL — RECURSIVE UPDATE
    # ============================================================
    def _recompute_recursive(self, identifier: str, visited: set):
        """
        DFS over formula dependency graph.

        Example:
            price change → value → total_portfolio_value → allocation_percentage
        """
        dependent_cols = self._find_formula_columns_depending_on(identifier)

        for col in dependent_cols:
            if col.identifier in visited:
                continue

            visited.add(col.identifier)

            # --- Recompute this formula column ---
            self._recompute_formula_column(col)

            # --- Then propagate to any formulas depending on it ---
            self._recompute_recursive(col.identifier, visited)

    # ============================================================
    # INTERNAL — find formula columns referencing an identifier
    # ============================================================
    def _find_formula_columns_depending_on(self, identifier: str):
        result = []

        for col in self.schema.columns.filter(source="formula"):
            if not col.formula:
                continue

            resolver = FormulaDependencyResolver(col.formula)
            deps = resolver.extract_identifiers()

            if identifier in deps:
                result.append(col)

        return result

    # ============================================================
    # INTERNAL — recompute a single formula column
    # ============================================================
    def _recompute_formula_column(self, column):
        """
        Compute NEW value for a computed formula column using SCV-first logic.
        Then store into SchemaColumnValue as formatted (rounded) string.
        """
        # Build SCV-first evaluation context
        resolver = FormulaDependencyResolver(column.formula)
        ctx = resolver.build_context(self.holding, self.schema)

        # Determine precision from constraints or formula
        precision = FormulaPrecisionResolver.get_precision(
            formula=column.formula,
            target_column=column,
        )

        # Evaluate formula
        result = FormulaEvaluator(
            formula=column.formula,
            context=ctx,
            precision=precision,
        ).evaluate()

        # Write SCV
        scv = SchemaColumnValue.objects.get(
            column=column,
            holding=self.holding
        )
        scv.value = str(result)
        scv.is_edited = False  # formula columns can never be "edited"
        scv.save(update_fields=["value", "is_edited"])
