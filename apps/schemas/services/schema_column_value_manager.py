from decimal import Decimal, ROUND_HALF_UP
from schemas.models.schema import SchemaColumnValue


class SchemaColumnValueManager:
    """
    PURE SCV VALUE MANAGER.

    Responsibilities:
        - Compute display values
        - Apply formatting & constraints
        - Persist SCV values
        - Preserve SOURCE_USER overrides

    NON-responsibilities:
        ❌ Trigger recomputation
        ❌ Traverse formula dependencies
        ❌ Call FormulaUpdateEngine
        ❌ Orchestrate schema refreshes

    All recomputation MUST be handled by:
        → SCVRefreshService → SchemaManager
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
        Recompute this SCV's display value ONLY.
        Caller decides whether this is allowed.
        """
        self.scv.value = self.display_for_column(
            self.column,
            self.holding,
        )

    # ============================================================
    # DISPLAY LOGIC (PURE)
    # ============================================================
    @staticmethod
    def display_for_column(column, holding):
        from schemas.services.formulas.resolver import FormulaDependencyResolver
        from schemas.services.formulas.evaluator import FormulaEvaluator
        from schemas.services.formulas.precision import FormulaPrecisionResolver

        # ---------------- FORMULA ----------------
        if column.source == "formula" and column.formula:
            resolver = FormulaDependencyResolver(column.formula)
            context = resolver.build_context(holding, column.schema)

            precision = FormulaPrecisionResolver.get_precision(
                formula=column.formula,
                target_column=column,
            )

            return str(
                FormulaEvaluator(
                    formula=column.formula,
                    context=context,
                    precision=precision,
                ).evaluate()
            )

        # ---------------- HOLDING ----------------
        if column.source == "holding" and column.source_field:
            raw = SchemaColumnValueManager._resolve_path(
                holding,
                column.source_field,
            )
            return SchemaColumnValueManager._format(column, raw)

        # ---------------- ASSET ----------------
        if column.source == "asset" and column.source_field:
            asset = holding.asset if holding else None
            raw = (
                SchemaColumnValueManager._resolve_path(asset, column.source_field)
                if asset
                else None
            )
            return SchemaColumnValueManager._format(column, raw)

        # ---------------- CUSTOM / EMPTY ----------------
        return SchemaColumnValueManager._static_default(column)

    # ============================================================
    # FORMATTING
    # ============================================================
    @staticmethod
    def _format(column, raw):
        if raw is None:
            return SchemaColumnValueManager._static_default(column)

        if column.data_type == "decimal":
            try:
                value = Decimal(str(raw))
            except Exception:
                return SchemaColumnValueManager._static_default(column)

            dp = SchemaColumnValueManager._decimal_places(column)

            try:
                quant = Decimal("1").scaleb(-dp)
                return str(value.quantize(quant, rounding=ROUND_HALF_UP))
            except Exception:
                return str(value)

        if column.data_type == "integer":
            try:
                return str(int(raw))
            except Exception:
                return "0"

        if column.data_type == "string":
            s = str(raw)
            max_len = SchemaColumnValueManager._max_length(column)
            return s[:max_len] if max_len else s

        return raw

    # ============================================================
    # CONSTRAINT HELPERS
    # ============================================================
    @staticmethod
    def _decimal_places(column):
        constraint = column.constraints_set.filter(name="decimal_places").first()
        try:
            return int(constraint.get_typed_value()) if constraint else 2
        except Exception:
            return 2

    @staticmethod
    def _max_length(column):
        constraint = column.constraints_set.filter(name="max_length").first()
        try:
            return int(constraint.get_typed_value()) if constraint else 255
        except Exception:
            return 255

    # ============================================================
    # USER EDIT API (NO CASCADE)
    # ============================================================
    def save_user_value(self, raw_value):
        """
        User explicitly overrides the SCV.

        ❗ Does NOT trigger recomputation.
        Caller must notify SCVRefreshService.
        """
        self.scv.value = self._format(self.column, raw_value)
        self.scv.source = SchemaColumnValue.SOURCE_USER
        self.scv.save(update_fields=["value", "source"])

    def revert_to_system(self):
        """
        Clear manual override and recompute local value.

        ❗ Does NOT trigger recomputation cascade.
        """
        self.refresh_display_value()

        self.scv.source = (
            SchemaColumnValue.SOURCE_FORMULA
            if self.column.source == "formula"
            else SchemaColumnValue.SOURCE_SYSTEM
        )
        self.scv.save(update_fields=["value", "source"])

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
    # FIELD RESOLUTION (PURE)
    # ============================================================
    @staticmethod
    def _resolve_path(obj, path):
        if not obj or not path:
            return None

        for part in path.split("__"):
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        return obj

    # ============================================================
    # SCV FACTORY
    # ============================================================
    @classmethod
    def get_or_create(cls, holding, column):
        scv, _ = SchemaColumnValue.objects.get_or_create(
            column=column,
            holding=holding,
            defaults={
                "value": cls.display_for_column(column, holding),
                "source": SchemaColumnValue.SOURCE_SYSTEM,
            },
        )
        return cls(scv)
