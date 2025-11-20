from schemas.models.schema import Schema, SchemaColumnValue
from schemas.services.formulas.evaluator import FormulaEvaluator
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.formulas.precision import FormulaPrecisionResolver


class FormulaUpdateEngine:
    """
    Recalculates all formula-based column values for a single holding
    whenever **any SCV value or raw holding value** changes.

    This engine handles:
      ✔ dependency resolution
      ✔ multi-step chained formulas
      ✔ SCV-first logic
      ✔ precision from formula or constraints
    """

    def __init__(self, holding, schema: Schema):
        self.holding = holding
        self.schema = schema

    # ============================================================
    # PUBLIC ENTRYPOINT
    # ============================================================
    def update_dependent_formulas(self, changed_identifier: str):
        """
        Trigger recalculation of formula columns that depend on `changed_identifier`.
        This naturally supports chained updates.
        """
        visited = set()
        self._recompute_recursive(changed_identifier, visited)

    # ============================================================
    # INTERNAL — recursive recomputation
    # ============================================================
    def _recompute_recursive(self, identifier: str, visited: set):
        """
        Recompute all formulas that reference this identifier.
        Prevents infinite loops via visited set.
        """
        dependent_cols = self._find_formula_columns_depending_on(identifier)

        for col in dependent_cols:
            if col.identifier in visited:
                continue

            visited.add(col.identifier)

            # --- recompute NOW ---
            self._recompute_formula_column(col)

            # --- now propagate ---
            self._recompute_recursive(col.identifier, visited)

    # ============================================================
    # INTERNAL — find formulas referencing an identifier
    # ============================================================
    def _find_formula_columns_depending_on(self, identifier: str):
        result = []

        for col in self.schema.columns.filter(source="formula"):
            formula = col.formula
            if not formula:
                continue

            resolver = FormulaDependencyResolver(formula)
            deps = resolver.extract_identifiers()

            if identifier in deps:
                result.append(col)

        return result

    # ============================================================
    # INTERNAL — recompute one formula column
    # ============================================================
    def _recompute_formula_column(self, column):
        resolver = FormulaDependencyResolver(column.formula)
        context = resolver.build_context(self.holding, self.schema)

        precision = FormulaPrecisionResolver.get_precision(column.formula)

        result = FormulaEvaluator(
            formula=column.formula,
            context=context,
            precision=precision
        ).evaluate()

        scv = SchemaColumnValue.objects.get(
            column=column, holding=self.holding)
        scv.value = str(result)
        scv.is_edited = False  # formulas cannot be “edited”
        scv.save(update_fields=["value", "is_edited"])
