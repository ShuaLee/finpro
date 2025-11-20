from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.formulas.precision import FormulaPrecisionResolver


class FormulaUpdateEngine:
    """
    Recalculates all formula-based column values for a single holding.
    """

    def __init__(self, holding, schema):
        self.holding = holding
        self.schema = schema

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------
    def update_dependent_formulas(self, changed_identifier: str):
        visited = set()
        self._recompute_recursive(changed_identifier, visited)

    # ------------------------------------------------------------
    # Recursive propagation
    # ------------------------------------------------------------
    def _recompute_recursive(self, identifier: str, visited: set):
        dependent_cols = self._find_formula_columns_depending_on(identifier)

        for col in dependent_cols:
            if col.identifier in visited:
                continue

            visited.add(col.identifier)

            self._recompute_formula_column(col)
            self._recompute_recursive(col.identifier, visited)

    # ------------------------------------------------------------
    # Find formula columns depending on identifier
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # Recompute a formula column
    # ------------------------------------------------------------
    def _recompute_formula_column(self, column):
        from schemas.models.schema import SchemaColumnValue
        from schemas.services.formulas.evaluator import FormulaEvaluator

        resolver = FormulaDependencyResolver(column.formula)
        context = resolver.build_context(self.holding, self.schema)

        precision = FormulaPrecisionResolver.get_precision(
            formula=column.formula,
            target_column=column,
        )

        result = FormulaEvaluator(
            formula=column.formula,
            context=context,
            precision=precision,
        ).evaluate()

        scv = SchemaColumnValue.objects.get(
            column=column,
            holding=self.holding,
        )
        scv.value = str(result)
        scv.is_edited = False
        scv.save(update_fields=["value", "is_edited"])
