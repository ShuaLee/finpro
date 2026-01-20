from decimal import Decimal
from typing import Dict, List
import ast

from django.core.exceptions import ValidationError

from schemas.models.formula import Formula
from schemas.models.schema import SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class FormulaDependencyResolver:
    """
    READ-ONLY resolver.
    Builds a numeric evaluation context for formulas.
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # ================================================================
    # IDENTIFIER EXTRACTION
    # ================================================================
    def extract_identifiers(self) -> List[str]:
        tree = ast.parse(self.formula.expression, mode="eval")
        return [
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
        ]

    # ================================================================
    # VALIDATION
    # ================================================================
    def validate_schema_columns_exist(self, schema):
        missing = [
            ident
            for ident in self.extract_identifiers()
            if not schema.columns.filter(identifier=ident).exists()
        ]

        if missing:
            raise ValidationError(
                f"Formula '{self.formula.identifier}' references missing columns: {missing}"
            )

    # ================================================================
    # CONTEXT BUILDING (SCV-FIRST, READ-ONLY)
    # ================================================================
    def build_context(self, holding, schema) -> Dict[str, Decimal]:
        """
        Build evaluation context:
        - SOURCE_USER → use stored SCV value
        - otherwise   → recompute display value
        """
        self.validate_schema_columns_exist(schema)

        ctx: Dict[str, Decimal] = {}

        for ident in self.extract_identifiers():
            column = schema.columns.get(identifier=ident)

            scv = SchemaColumnValue.objects.filter(
                column=column,
                holding=holding,
            ).first()

            if not scv:
                raise ValidationError(
                    f"Missing SchemaColumnValue for '{ident}' "
                    f"(holding={holding.id})"
                )

            # ---------------- USER OVERRIDE ----------------
            if scv.source == SchemaColumnValue.SOURCE_USER:
                ctx[ident] = Decimal(str(scv.value))
                continue

            # ---------------- SYSTEM / FORMULA ----------------
            mgr = SchemaColumnValueManager(scv)
            value = mgr.display_for_column(column, holding)

            ctx[ident] = Decimal(str(value))

        return ctx

    # ================================================================
    # CYCLE DETECTION
    # ================================================================
    def detect_cycles(self, schema, start_identifier: str):
        visited = set()
        self._dfs(schema, start_identifier, visited)

    def _dfs(self, schema, identifier, visited):
        if identifier in visited:
            raise ValidationError(
                f"Formula dependency cycle detected involving '{identifier}'."
            )

        visited.add(identifier)

        col = schema.columns.filter(identifier=identifier).first()
        if not col or not col.formula:
            return

        resolver = FormulaDependencyResolver(col.formula)
        for dep in resolver.extract_identifiers():
            self._dfs(schema, dep, visited.copy())
