from decimal import Decimal, ROUND_HALF_UP
from schemas.models.schema import SchemaColumnValue


class SchemaColumnValueManager:
    """
    SCV Manager:
      - Computes display values
      - NEVER decides whether to recompute (SchemaManager does that)
      - Applies constraints (decimal places, max_length, etc.)
      - Preserves SOURCE_USER values
    """

    def __init__(self, scv: SchemaColumnValue):
        self.scv = scv
        self.column = scv.column
        self.holding = scv.holding

    # ============================================================
    # DISPLAY ENTRY POINT (PURE)
    # ============================================================
    def refresh_display_value(self):
        """
        Recompute the SCV value ONLY.
        Caller decides whether this is allowed.
        """
        self.scv.value = self.display_for_column(
            self.column,
            self.holding,
        )

    # ============================================================
    # DISPLAY LOGIC
    # ============================================================
    @staticmethod
    def display_for_column(column, holding):
        from schemas.services.formulas.resolver import FormulaDependencyResolver
        from schemas.services.formulas.evaluator import FormulaEvaluator
        from schemas.services.formulas.precision import FormulaPrecisionResolver

        # ---------------- FORMULA ----------------
        if column.source == "formula" and column.formula:
            resolver = FormulaDependencyResolver(column.formula)
            ctx = resolver.build_context(holding, column.schema)

            precision = FormulaPrecisionResolver.get_precision(
                formula=column.formula,
                target_column=column,
            )

            return str(
                FormulaEvaluator(
                    formula=column.formula,
                    context=ctx,
                    precision=precision,
                ).evaluate()
            )

        # ---------------- HOLDING ----------------
        if column.source == "holding" and column.source_field:
            raw = SchemaColumnValueManager._resolve_path(
                holding,
                column.source_field,
            )
            return SchemaColumnValueManager._format(column, raw, holding)

        # ---------------- ASSET ----------------
        if column.source == "asset" and column.source_field:
            asset = holding.asset if holding else None
            raw = (
                SchemaColumnValueManager._resolve_path(
                    asset, column.source_field)
                if asset
                else None
            )
            return SchemaColumnValueManager._format(column, raw, holding)

        # ---------------- CUSTOM / EMPTY ----------------
        return SchemaColumnValueManager._static_default(column)

    # ============================================================
    # FORMATTING
    # ============================================================
    @staticmethod
    def _format(column, raw, holding):
        if raw is None:
            return SchemaColumnValueManager._static_default(column)

        if column.data_type == "decimal":
            try:
                val = Decimal(str(raw))
            except Exception:
                return raw

            dp = SchemaColumnValueManager._decimal_places(column, holding)

            try:
                quant = Decimal("1").scaleb(-int(dp))
                return str(val.quantize(quant, rounding=ROUND_HALF_UP))
            except Exception:
                # Absolute fallback — never break SCV creation
                return str(val)

        if column.data_type == "integer":
            try:
                return str(int(raw))
            except Exception:
                return raw

        if column.data_type == "string":
            s = str(raw)
            max_len = SchemaColumnValueManager._max_length(column)
            return s[:max_len] if max_len else s

        return raw

    # ============================================================
    # CONSTRAINT HELPERS
    # ============================================================
    @staticmethod
    def _decimal_places(column, holding=None):
        """
        Always return a safe integer decimal place count.
        """
        c = column.constraints_set.filter(name="decimal_places").first()

        if not c:
            return 2

        try:
            value = c.get_typed_value()
            if value is None:
                return 2
            return int(value)
        except (TypeError, ValueError):
            return 2

    @staticmethod
    def _max_length(column):
        c = column.constraints_set.filter(name="max_length").first()
        return c.get_typed_value() if c else 255

    # ============================================================
    # USER EDIT API
    # ============================================================
    def save_user_value(self, raw_value):
        """
        User explicitly overrides the SCV.
        """
        formatted = self._format(self.column, raw_value, self.holding)

        self.scv.value = formatted
        self.scv.source = SchemaColumnValue.SOURCE_USER
        self.scv.save(update_fields=["value", "source"])

        self._trigger_formula_updates(self.column.identifier)

    def revert_to_system(self):
        """
        User clears manual override.
        """
        self.refresh_display_value()

        self.scv.source = (
            SchemaColumnValue.SOURCE_FORMULA
            if self.column.source == "formula"
            else SchemaColumnValue.SOURCE_SYSTEM
        )
        self.scv.save(update_fields=["value", "source"])

        self._trigger_formula_updates(self.column.identifier)

    # ============================================================
    # FORMULA CASCADE
    # ============================================================
    def _trigger_formula_updates(self, changed_identifier):
        from schemas.services.formulas.update_engine import FormulaUpdateEngine

        engine = FormulaUpdateEngine(self.holding, self.column.schema)
        engine.update_dependent_formulas(changed_identifier)

    # ============================================================
    # STATIC DEFAULTS
    # ============================================================
    @staticmethod
    def _static_default(column):
        if column.data_type == "decimal":
            return "0.00"
        if column.data_type == "integer":
            return "0"
        if column.data_type == "string":
            return "-"
        return None

    # ============================================================
    # FIELD RESOLUTION
    # ============================================================
    @staticmethod
    def _resolve_path(obj, path):
        if not obj or not path:
            return None

        print(f"Resolving path: {path}")
        print(f"Initial obj: {obj}")

        for part in path.split("__"):
            obj = getattr(obj, part, None)
            print(f" → {part}: {obj}")
            if obj is None:
                return None
        return obj

    @classmethod
    def get_or_create(cls, holding, column):
        initial_value = cls.display_for_column(column, holding)

        scv, created = SchemaColumnValue.objects.get_or_create(
            column=column,
            holding=holding,
            defaults={"value": initial_value,
                      "source": SchemaColumnValue.SOURCE_SYSTEM},
        )
        return cls(scv)
