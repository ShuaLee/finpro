from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Prefetch

from assets.models.core import AssetType
from formulas.services.formula_resolver import FormulaResolver
from fx.models.fx import FXCurrency
from schemas.models.schema_column_asset_behaviour import SchemaColumnAssetBehaviour
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import SchemaColumnTemplateBehaviour


class SchemaQueryService:
    @staticmethod
    def resolve_enum_values(constraint, *, column=None, holding=None) -> list[str]:
        if constraint.name != "enum":
            return []

        enum_key = constraint.value_string
        if enum_key == "fx_currency":
            return list(FXCurrency.objects.order_by("code").values_list("code", flat=True))

        if enum_key and "," in enum_key:
            return [v.strip() for v in enum_key.split(",") if v.strip()]

        return []

    # old-name compatibility
    resolve = resolve_enum_values

    @staticmethod
    def dependency_graph(*, schema) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = defaultdict(set)

        behaviors = SchemaColumnAssetBehaviour.objects.filter(
            column__schema=schema,
            source="formula",
        ).select_related("column", "formula_definition__formula")

        for behavior in behaviors:
            if not behavior.formula_definition:
                continue

            formula = behavior.formula_definition.formula
            dependent = behavior.column.identifier

            for dep in formula.dependencies:
                if FormulaResolver.is_implicit(dep):
                    continue
                graph[dep].add(dependent)

        return graph

    # old-name compatibility
    build = dependency_graph

    @staticmethod
    def dependents_of(*, schema, identifier: str) -> set[str]:
        return SchemaQueryService.dependency_graph(schema=schema).get(identifier, set())

    @staticmethod
    def dependencies_of(*, schema, identifier: str) -> set[str]:
        graph = SchemaQueryService.dependency_graph(schema=schema)
        deps = set()
        for src, targets in graph.items():
            if identifier in targets:
                deps.add(src)
        return deps

    @staticmethod
    def is_dependency(*, schema, identifier: str) -> bool:
        return bool(SchemaQueryService.dependents_of(schema=schema, identifier=identifier))

    @staticmethod
    def as_dot(*, schema) -> str:
        graph = SchemaQueryService.dependency_graph(schema=schema)
        lines = ["digraph SchemaColumnDependencies {"]
        for src, targets in graph.items():
            for target in sorted(targets):
                lines.append(f'    "{src}" -> "{target}";')
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def as_mermaid(*, schema) -> str:
        graph = SchemaQueryService.dependency_graph(schema=schema)
        lines = ["graph TD"]
        for src, targets in graph.items():
            for target in sorted(targets):
                lines.append(f"    {src} --> {target}")
        return "\n".join(lines)

    @staticmethod
    def list_available_templates_grouped(*, schema) -> dict[str, list]:
        existing = set(schema.columns.values_list("identifier", flat=True))
        allowed_asset_types = AssetType.objects.filter(
            account_types=schema.account_type)

        templates = (
            SchemaColumnTemplate.objects.filter(
                is_system=True, category__isnull=False)
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "behaviours",
                    queryset=SchemaColumnTemplateBehaviour.objects.filter(
                        asset_type__in=allowed_asset_types
                    ),
                )
            )
            .order_by("category__display_order", "category__name", "identifier")
        )

        if existing:
            templates = templates.exclude(identifier__in=existing)

        grouped = defaultdict(list)
        for template in templates:
            if not template.behaviours.all():
                continue
            grouped[template.category.identifier].append(template)

        return dict(grouped)

    # old-name compatibility
    list_available_grouped = list_available_templates_grouped

    @staticmethod
    def display_value_for_scv(scv):
        raw = scv.value
        dt = scv.column.data_type

        if raw in (None, "", "None"):
            if dt == "decimal":
                return "0.00"
            if dt == "percent":
                return "0.00%"
            if dt in ("string", "date"):
                return "-"
            if dt == "boolean":
                return "False"
            return None

        if dt == "decimal":
            return SchemaQueryService._format_decimal(raw, scv.column)

        if dt == "percent":
            return SchemaQueryService._format_percent(raw, scv.column)

        if dt == "boolean":
            val = str(raw).strip().lower()
            return "True" if val in ("true", "1", "yes") else "False"

        if dt == "date":
            if isinstance(raw, date):
                return raw.isoformat()
            try:
                return date.fromisoformat(str(raw)).isoformat()
            except Exception:
                return "-"

        return str(raw)

    @staticmethod
    def _decimal_places(column) -> int:
        constraint = column.constraints.filter(name="decimal_places").first()
        if not constraint:
            return 2
        try:
            return int(constraint.get_typed_value())
        except Exception:
            return 2

    @staticmethod
    def _format_decimal(raw, column) -> str:
        places = SchemaQueryService._decimal_places(column)
        quant = Decimal("1").scaleb(-places)
        value = Decimal(str(raw)).quantize(quant, rounding=ROUND_HALF_UP)
        return str(value)

    @staticmethod
    def _format_percent(raw, column) -> str:
        places = SchemaQueryService._decimal_places(column)
        quant = Decimal("1").scaleb(-places)
        value = (Decimal(str(raw)) * Decimal("100")
                 ).quantize(quant, rounding=ROUND_HALF_UP)
        return f"{value}%"
