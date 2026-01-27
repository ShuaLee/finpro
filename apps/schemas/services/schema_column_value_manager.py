from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.core.exceptions import ValidationError

from schemas.models.schema_column_asset_behaviour import SchemaColumnAssetBehaviour
from schemas.models.schema_column_value import SchemaColumnValue
from formulas.services.formula_resolver import FormulaResolver
from formulas.services.formula_evaluator import FormulaEvaluator
from fx.models.fx import FXRate


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
        self.asset = self.holding.asset if self.holding else None
        self.asset_type = self.asset.asset_type if self.asset else None

    # ============================================================
    # STRUCTURAL HELPERS
    # ============================================================
    @staticmethod
    def ensure_for_column(column):
        """
        Ensure SchemaColumnValues exist for this column across all holdings.

        - Structural only
        - Idempotent
        - Does NOT compute values
        - Does NOT trigger recomputation
        """

        schema = column.schema

        accounts = (
            schema.portfolio.accounts
            .filter(account_type=schema.account_type)
            .prefetch_related("holdings")
        )

        scvs_to_create = []

        for account in accounts:
            for holding in account.holdings.all():
                if not SchemaColumnValue.objects.filter(
                    column=column,
                    holding=holding,
                ).exists():
                    scvs_to_create.append(
                        SchemaColumnValue(
                            column=column,
                            holding=holding,
                            value=None,  # value will be computed later
                            source=SchemaColumnValue.Source.SYSTEM,
                        )
                    )

        if scvs_to_create:
            SchemaColumnValue.objects.bulk_create(scvs_to_create)

    # ============================================================
    # PUBLIC
    # ============================================================
    def refresh_display_value(self) -> None:
        self.scv.value = self._compute_value()

    # ============================================================
    # CORE
    # ============================================================
    def _compute_value(self) -> str | None:
        if not self.asset_type:
            return self._static_default()

        behavior = self.column.behavior_for(self.asset_type)
        if not behavior:
            return self._static_default()

        source = behavior.source

        # ---------------- FORMULA ----------------
        if source == "formula" and behavior.formula_definition:
            return self._compute_formula_value(behavior)

        # ---------------- HOLDING ----------------
        if source == "holding" and behavior.source_field:
            raw = self._resolve_path(self.holding, behavior.source_field)
            return self._format_value(raw)

        # ---------------- ASSET ----------------
        if source == "asset" and behavior.source_field:
            raw = self._resolve_path(self.asset, behavior.source_field)
            return self._format_value(raw)

        # ---------------- CONSTANT ----------------
        if source == "constant":
            return self._format_value(behavior.constant_value)

        # ---------------- USER / UNDEFINED ----------------
        return self._static_default()

    # ============================================================
    # FORMULA
    # ============================================================
    def _compute_formula_value(
        self, behavior: SchemaColumnAssetBehaviour
    ) -> str | None:
        definition = behavior.formula_definition
        formula = definition.formula

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

    def _build_context(self) -> dict[str, Decimal]:
        schema = self.column.schema
        holding = self.holding

        context: dict[str, Decimal] = {}

        # --------------------------------------------------
        # 1. SCV-based identifiers
        # --------------------------------------------------
        scvs = SchemaColumnValue.objects.filter(
            holding=holding,
            column__schema=schema,
        ).select_related("column")

        for scv in scvs:
            try:
                context[scv.column.identifier] = Decimal(str(scv.value))
            except Exception:
                context[scv.column.identifier] = Decimal("0")

        # --------------------------------------------------
        # 2. Inject FX rate (runtime-only)
        # --------------------------------------------------
        asset = holding.asset
        profile = holding.account.portfolio.profile

        asset_currency = getattr(asset, "currency", None)
        profile_currency = getattr(profile, "currency", None)

        if asset_currency and profile_currency:
            if asset_currency == profile_currency:
                fx_rate = Decimal("1")
            else:
                fx = FXRate.objects.filter(
                    from_currency__code=asset_currency,
                    to_currency__code=profile_currency,
                ).order_by("-created_at").first()

                if not fx:
                    raise ValidationError(
                        f"No FX rate found for {asset_currency} → {profile_currency}"
                    )

                fx_rate = Decimal(str(fx.rate))
        else:
            fx_rate = Decimal("1")

        context["fx_rate"] = fx_rate

        return context

    # ============================================================
    # FORMATTING
    # ============================================================

    def _format_value(self, raw: Any) -> str | None:
        if raw is None:
            return self._static_default()

        dt = self.column.data_type

        try:
            if dt == "decimal":
                return self._format_decimal(Decimal(str(raw)))
            if dt == "integer":
                return str(int(raw))
            if dt == "boolean":
                return str(bool(raw))
            return str(raw)
        except Exception:
            return self._static_default()

    def _format_decimal(self, value: Decimal) -> str:
        places = self._decimal_places()
        quant = Decimal("1").scaleb(-places)
        return str(value.quantize(quant, rounding=ROUND_HALF_UP))

    # ============================================================
    # CONSTRAINTS
    # ============================================================
    def _decimal_places(self) -> int:
        constraint = self.column.constraints.filter(
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
        dt = self.column.data_type
        if dt == "decimal":
            return "0.00"
        if dt == "integer":
            return "0"
        if dt == "boolean":
            return "False"
        if dt == "string":
            return "-"
        return None

    # ============================================================
    # PATH
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
