from collections import defaultdict

from schemas.models.schema_column_asset_behaviour import (
    SchemaColumnAssetBehaviour,
)
from formulas.services.formula_resolver import FormulaResolver


class SchemaColumnDependencyGraph:
    """
    Read-only dependency graph for SchemaColumns.

    Edge direction:
        A -> B  means "B depends on A"

    Graph is schema-local and formula-only.
    """

    # ======================================================
    # GRAPH BUILDING
    # ======================================================
    @staticmethod
    def build(*, schema) -> dict[str, set[str]]:
        """
        Build adjacency list:

        {
            "quantity": {"market_value"},
            "market_value": {"current_value"},
        }
        """
        graph: dict[str, set[str]] = defaultdict(set)

        behaviours = SchemaColumnAssetBehaviour.objects.filter(
            column__schema=schema,
            source="formula",
        ).select_related(
            "column",
            "formula_definition__formula",
        )

        for behaviour in behaviours:
            formula = behaviour.formula_definition.formula
            dependents = behaviour.column.identifier

            for dep in FormulaResolver.required_identifiers(formula):
                if FormulaResolver.is_implicit(dep):
                    continue

                graph[dep].add(dependents)

        return graph

    # ======================================================
    # QUERY HELPERS
    # ======================================================
    @staticmethod
    def dependents_of(*, schema, identifier: str) -> set[str]:
        """
        Columns that depend on `identifier`.
        """
        return SchemaColumnDependencyGraph.build(
            schema=schema
        ).get(identifier, set())

    @staticmethod
    def dependencies_of(*, schema, identifier: str) -> set[str]:
        """
        Columns that `identifier` depends on.
        """
        graph = SchemaColumnDependencyGraph.build(schema=schema)

        deps = set()
        for src, targets in graph.items():
            if identifier in targets:
                deps.add(src)

        return deps

    @staticmethod
    def is_dependency(*, schema, identifier: str) -> bool:
        """
        True if any column depends on this identifier.
        """
        return bool(
            SchemaColumnDependencyGraph.dependents_of(
                schema=schema,
                identifier=identifier,
            )
        )

    # ======================================================
    # VISUALIZATION
    # ======================================================
    @staticmethod
    def as_dot(*, schema) -> str:
        """
        Graphviz DOT output.
        """
        graph = SchemaColumnDependencyGraph.build(schema=schema)

        lines = ["digraph SchemaColumnDependencies {"]

        for src, targets in graph.items():
            for target in targets:
                lines.append(f'    "{src}" -> "{target}";')

        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def as_mermaid(*, schema) -> str:
        """
        Mermaid.js flowchart output.
        """
        graph = SchemaColumnDependencyGraph.build(schema=schema)

        lines = ["graph TD"]

        for src, targets in graph.items():
            for target in targets:
                lines.append(f"    {src} --> {target}")

        return "\n".join(lines)
