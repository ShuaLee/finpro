from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from schemas.models.schema_column_value import SchemaColumnValue
from formulas.services.formula_resolver import FormulaResolver
from formulas.services.formula_evaluator import FormulaEvaluator


class SchemaColumnValueManager:
    """
    PURE SCV computation manager.

    Responsibilities:
        - Compute the display value for ONE SchemaColumnValue
        - Apply formatting and precision
        - Invoke formula execution when needed

    Non-responsibilities:
        ❌ Trigger recomputation
        ❌ Traverse schemas or holdings
        ❌ Resolve schema dependencies
        ❌ Persist SCVs outside the one managed instance
    """

    def __init__(self, scv: SchemaColumnValue):
        self.scv = scv
        self.column = scv.column
        self.holding = scv.holding

    # ============================================================
    # PUBLIC ENTRY POINT
    # ============================================================
    def refresh_display_value(self) -> None:
        """
        Recompute and assign this SCV's value.

        Caller is responsible for:
            - deciding whether recomputation is allowed
            - persisting source changes
        """
        self.scv.value = self._compute_value()

    # ============================================================
    # CORE COMPUTATION
    # ============================================================
    def _compute_value(self) -> str | None:
        column = self.column

        # ---------------- FORMULA ----------------
        if column.source == "formula" and column.formula_definition:
            return self._compute_formula_value()

        # ---------------- HOLDING ----------------
        if column.source == "holding" and column.source_field:
            raw = self._resolve_path(self.holding, column.source_field)
            return self._format_value(raw)

        # ---------------- ASSET ----------------
        if column.source == "asset" and column.source_field:
            asset = self.holding.asset if self.holding else None
            raw = self._resolve_path(
                asset, column.source_field) if asset else None
            return self._format_value(raw)

        # ---------------- CUSTOM / EMPTY ----------------
        return self._static_default()

    # ============================================================
    # FORMULA COMPUTATION
    # ============================================================
    def _compute_formula_value(self) -> str:
        definition = self.column.formula_definition
        formula = definition.formula

        # Build evaluation context
        context = FormulaResolver.resolve_inputs(
            formula=formula,
            context=self._build_context(),
            allow_missing=(definition.dependency_policy == "auto_expand"),
            default_missing=Decimal("0"),
        )

        result = FormulaEvaluator.evaluate(
            formula=formula,
            context=context,
        )

        return self._format_decimal(result)

    def _build_context(self) -> dict[str, Any]:
        """
        Build identifier → raw value mapping for formula evaluation
        from existing SCVs in the same schema.
        """
        schema = self.column.schema
        holding = self.holding

        context = {}

        for scv in SchemaColumnValue.objects.filter(
            holding=holding,
            column__schema=schema,
        ).select_related("column"):
            identifier = scv.column.identifier
            try:
                context[identifier] = Decimal(str(scv.value))
            except Exception:
                context[identifier] = Decimal("0")

        return context

    # ============================================================
    # FORMATTING
    # ============================================================
    def _format_value(self, raw: Any) -> str | None:
        if raw is None:
            return self._static_default()

        if self.column.data_type == "decimal":
            try:
                return self._format_decimal(Decimal(str(raw)))
            except Exception:
                return self._static_default()

        if self.column.data_type == "integer":
            try:
                return str(int(raw))
            except Exception:
                return "0"

        if self.column.data_type == "string":
            return str(raw)

        if self.column.data_type == "boolean":
            return str(bool(raw))

        return str(raw)

    def _format_decimal(self, value: Decimal) -> str:
        places = self._decimal_places()
        quant = Decimal("1").scaleb(-places)
        return str(value.quantize(quant, rounding=ROUND_HALF_UP))

    # ============================================================
    # CONSTRAINT HELPERS (READ-ONLY)
    # ============================================================
    def _decimal_places(self) -> int:
        constraint = self.column.constraints_set.filter(
            name="decimal_places"
        ).first()

        try:
            return int(constraint.get_typed_value()) if constraint else 2
        except Exception:
            return 2

    # ============================================================
    # DEFAULTS
    # ============================================================
    def _static_default(self) -> str | None:
        if self.column.data_type == "decimal":
            return "0.00"
        if self.column.data_type == "integer":
            return "0"
        if self.column.data_type == "string":
            return "-"
        if self.column.data_type == "boolean":
            return "False"
        return None

    # ============================================================
    # PATH RESOLUTION (PURE)
    # ============================================================
    @staticmethod
    def _resolve_path(obj, path: str | None) -> Any:
        if not obj or not path:
            return None

        for part in path.split("__"):
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        return obj
