from __future__ import annotations

from collections import defaultdict, deque
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError

from formulas.services.formula_evaluator import FormulaEvaluator
from formulas.services.formula_resolver import FormulaResolver
from fx.models.fx import FXCurrency, FXRate
from schemas.models import Schema, SchemaColumnValue


class SchemaEngine:
    """
    Deterministic schema compute engine.

    Responsibilities:
    - Ensure SCVs exist for a holding
    - Recompute non-user SCVs
    - Preserve valid user overrides
    - Revert invalid enum overrides
    - Execute formula columns with dependency-aware ordering
    """

    def __init__(self, schema: Schema):
        self.schema = schema
        self._columns_cache = None

    @classmethod
    def for_account(cls, account) -> "SchemaEngine":
        schema = getattr(account, "active_schema", None)
        if not schema:
            raise ValueError(f"No active schema for account '{account}'.")
        return cls(schema)

    @property
    def columns(self):
        if self._columns_cache is None:
            self._columns_cache = list(
                self.schema.columns.prefetch_related(
                    "asset_behaviors", "constraints")
            )
        return self._columns_cache

    def sync_scvs_for_holding(self, holding) -> None:
        ordered_columns = self._topologically_ordered_columns()

        for column in ordered_columns:
            scv, _ = SchemaColumnValue.objects.get_or_create(
                column=column,
                holding=holding,
                defaults={
                    "value": None,
                    "source": SchemaColumnValue.Source.SYSTEM,
                },
            )
            self._recompute_scv(scv, column)

    def resequence(self) -> None:
        for i, col in enumerate(
            self.schema.columns.order_by("display_order", "id"),
            start=1,
        ):
            if col.display_order != i:
                col.display_order = i
                col.save(update_fields=["display_order"])

    # ---------------------------------------------------------
    # Core recompute
    # ---------------------------------------------------------

    def _recompute_scv(self, scv: SchemaColumnValue, column) -> None:
        # 0) If user override is now invalid enum, revert it then continue recompute.
        if scv.source == SchemaColumnValue.Source.USER:
            enum_constraint = column.constraints.filter(name="enum").first()
            if enum_constraint:
                allowed = self._resolve_enum_allowed_values(
                    enum_constraint,
                    column=column,
                    holding=scv.holding,
                )
                if allowed and scv.value not in allowed:
                    scv.value = None
                    scv.source = SchemaColumnValue.Source.SYSTEM
                    scv.save(update_fields=["value", "source"])

        # 1) Respect valid user overrides.
        if scv.source == SchemaColumnValue.Source.USER:
            return

        # 2) Compute fresh value.
        raw_value, computed_source = self._compute_raw_value_and_source(
            scv, column)

        scv.value = self._serialize_value(raw_value)
        scv.source = computed_source
        scv.save(update_fields=["value", "source"])

    def _compute_raw_value_and_source(self, scv: SchemaColumnValue, column):
        holding = scv.holding
        asset = holding.asset if holding else None
        asset_type = asset.asset_type if asset else None

        behavior = column.behavior_for(asset_type) if asset_type else None
        if not behavior:
            return None, SchemaColumnValue.Source.SYSTEM

        if behavior.source == "formula":
            result = self._compute_formula_raw_value(
                scv=scv, behavior=behavior)
            return result, SchemaColumnValue.Source.FORMULA

        if behavior.source == "holding" and behavior.source_field:
            return self._resolve_path(holding, behavior.source_field), SchemaColumnValue.Source.SYSTEM

        if behavior.source == "asset" and behavior.source_field:
            return self._resolve_path(asset, behavior.source_field), SchemaColumnValue.Source.SYSTEM

        if behavior.source == "constant":
            return behavior.constant_value, SchemaColumnValue.Source.SYSTEM

        return None, SchemaColumnValue.Source.SYSTEM

    # ---------------------------------------------------------
    # Formula execution
    # ---------------------------------------------------------

    def _compute_formula_raw_value(self, *, scv: SchemaColumnValue, behavior):
        definition = behavior.formula_definition
        if not definition:
            return None

        formula = definition.formula

        context = self._build_formula_context(
            formula=formula,
            holding=scv.holding,
        )

        resolved = FormulaResolver.resolve_inputs(
            formula=formula,
            context=context,
            allow_missing=(definition.dependency_policy == "auto_expand"),
            default_missing=Decimal("0"),
        )

        try:
            result = FormulaEvaluator.evaluate(
                formula=formula,
                context=resolved,
            )
        except Exception:
            return None

        if result is None:
            return None

        try:
            return Decimal(str(result))
        except Exception:
            return None

    def _build_formula_context(self, *, formula, holding) -> dict[str, Decimal]:
        context: dict[str, Decimal] = {}

        # Pull already-computed SCVs for this holding in this schema.
        scvs = (
            SchemaColumnValue.objects.filter(
                holding=holding,
                column__schema=self.schema,
            )
            .select_related("column")
        )
        scv_by_identifier = {scv.column.identifier: scv.value for scv in scvs}

        for identifier in formula.dependencies:
            if FormulaResolver.is_implicit(identifier):
                continue

            raw = scv_by_identifier.get(identifier)
            if raw in (None, "", "None"):
                continue

            try:
                context[identifier] = Decimal(str(raw))
            except Exception:
                # Leave missing so resolver can apply strict/auto_expand policy.
                continue

        if "fx_rate" in formula.dependencies:
            context["fx_rate"] = self._resolve_fx_rate(holding)

        return context

    def _resolve_fx_rate(self, holding) -> Decimal:
        asset = getattr(holding, "asset", None)
        if not asset:
            return Decimal("1")

        extension = getattr(asset, "extension", None)
        asset_currency = getattr(
            getattr(extension, "currency", None), "code", None)
        profile_currency = getattr(
            getattr(getattr(holding.account, "portfolio", None), "profile", None),
            "currency",
            None,
        )
        profile_currency_code = getattr(profile_currency, "code", None)

        if not asset_currency or not profile_currency_code:
            return Decimal("1")

        if asset_currency == profile_currency_code:
            return Decimal("1")

        fx = (
            FXRate.objects.filter(
                from_currency__code=asset_currency,
                to_currency__code=profile_currency_code,
            )
            .order_by("-updated_at")
            .first()
        )
        if not fx:
            raise ValidationError(
                f"No FX rate found for {asset_currency} -> {profile_currency_code}"
            )

        return Decimal(str(fx.rate))

    # ---------------------------------------------------------
    # Dependency ordering
    # ---------------------------------------------------------

    def _topologically_ordered_columns(self):
        columns = self.columns
        index = {c.identifier: i for i, c in enumerate(columns)}
        by_identifier = {c.identifier: c for c in columns}

        indegree = {c.identifier: 0 for c in columns}
        graph = defaultdict(set)

        for column in columns:
            behaviors = list(column.asset_behaviors.select_related(
                "formula_definition__formula"))
            for behavior in behaviors:
                if behavior.source != "formula" or not behavior.formula_definition:
                    continue

                formula = behavior.formula_definition.formula
                for dep in formula.dependencies:
                    if FormulaResolver.is_implicit(dep):
                        continue
                    if dep not in by_identifier:
                        continue
                    # dep -> column
                    if column.identifier not in graph[dep]:
                        graph[dep].add(column.identifier)
                        indegree[column.identifier] += 1

        queue = deque(
            sorted(
                [identifier for identifier, deg in indegree.items() if deg == 0],
                key=lambda ident: (
                    by_identifier[ident].display_order, index[ident]),
            )
        )

        ordered_ids = []
        while queue:
            ident = queue.popleft()
            ordered_ids.append(ident)

            for nxt in sorted(
                graph.get(ident, set()),
                key=lambda x: (by_identifier[x].display_order, index[x]),
            ):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        # Cycle fallback: keep deterministic order.
        if len(ordered_ids) != len(columns):
            remaining = [
                c.identifier for c in sorted(columns, key=lambda c: (c.display_order, c.id))
                if c.identifier not in set(ordered_ids)
            ]
            ordered_ids.extend(remaining)

        return [by_identifier[i] for i in ordered_ids]

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _resolve_path(obj, path: str | None) -> Any:
        if not obj or not path:
            return None

        current = obj
        for part in path.split("__"):
            current = getattr(current, part, None)
            if current is None:
                return None
        return current

    @staticmethod
    def _serialize_value(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return str(value)
        return str(value)

    @staticmethod
    def _resolve_enum_allowed_values(constraint, *, column=None, holding=None) -> list[str]:
        # Mirrors old behavior, but localized so engine does not depend on queries.py yet.
        if constraint.name != "enum":
            return []

        enum_key = constraint.value_string
        if enum_key == "fx_currency":
            return list(
                FXCurrency.objects.order_by(
                    "code").values_list("code", flat=True)
            )

        # Optional generic fallback: CSV static enum.
        if enum_key and "," in enum_key:
            return [v.strip() for v in enum_key.split(",") if v.strip()]

        return []
