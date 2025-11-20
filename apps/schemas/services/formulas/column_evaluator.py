from decimal import Decimal
from typing import Optional, Any

from schemas.models.schema import SchemaColumn
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.formulas.evaluator import FormulaEvaluator
from schemas.services.formulas.precision import FormulaPrecisionResolver


class SchemaColumnEvaluator:
    """
    Unified evaluation service for ANY SchemaColumn:

        ✔ Edited SCV override
        ✔ Formula evaluation (recursive, SCV-first)
        ✔ Holding source field
        ✔ Asset source field
        ✔ Constraints: decimal_places, max_length, etc.
        ✔ Static defaults

    Used by:
        - FormulaUpdateEngine
        - SCV Manager
        - Frontend APIs
        - Admin previews
        - Schema template initializer
        - Tests
    """

    def __init__(self, holding, column: SchemaColumn):
        self.holding = holding
        self.column = column

    # =======================================================
    # PUBLIC API
    # =======================================================
    def evaluate(self) -> Any:
        """
        Return final formatted value (string, int, decimal).
        """
        scv_manager = SchemaColumnValueManager.get_or_create(
            self.holding, self.column
        )
        scv = scv_manager.scv

        # ------------------------------------------
        # 1. USER-EDITED SCV OVERRIDES EVERYTHING
        # ------------------------------------------
        if scv.is_edited:
            return scv.value

        # ------------------------------------------
        # 2. FORMULA COLUMN
        # ------------------------------------------
        if self.column.formula:
            return self._evaluate_formula_column()

        # ------------------------------------------
        # 3. NORMAL HOLDING/ASSET SOURCED COLUMN
        # ------------------------------------------
        raw_value = self._raw_backend_value()

        if raw_value is None:
            return SchemaColumnValueManager._static_default(self.column)

        # Format using column constraints
        return SchemaColumnValueManager._apply_display_constraints(
            self.column,
            raw_value,
            self.holding
        )

    # =======================================================
    # INTERNAL HELPERS
    # =======================================================
    def _evaluate_formula_column(self):
        """
        Evaluate formula with SCV-first context and precision rules.
        """
        formula = self.column.formula

        # Build dependency context (SCV-first)
        ctx = FormulaDependencyResolver(formula).build_context(
            holding=self.holding,
            schema=self.column.schema,
        )

        precision = FormulaPrecisionResolver.get_precision(
            formula=formula,
            target_column=self.column,
        )

        return str(
            FormulaEvaluator(
                formula=formula,
                context=ctx,
                precision=precision
            ).evaluate()
        )

    def _raw_backend_value(self) -> Optional[Any]:
        """
        For holding/asset sourced columns, fetch raw backend value.
        """
        col = self.column

        # Holding-sourced
        if col.source == "holding" and col.source_field:
            return getattr(self.holding, col.source_field, None)

        # Asset-sourced
        if col.source == "asset" and col.source_field:
            asset = getattr(self.holding, "asset", None)
            if asset:
                return SchemaColumnValueManager._resolve_path(
                    asset,
                    col.source_field
                )

        return None
