from decimal import Decimal
from typing import Dict, List, Set
import ast

from django.core.exceptions import ValidationError

from schemas.models.formula import Formula
from schemas.models.schema import SchemaColumnValue
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class FormulaDependencyResolver:
    """
    READ-ONLY formula analyzer.

    Responsibilities:
        - Extract identifiers from a formula
        - Validate schema compatibility
        - Build numeric evaluation context
        - Detect dependency cycles

    This class MUST remain side-effect free.
    """

    def __init__(self, formula: Formula):
        self.formula = formula
        self._identifiers: Set[str] | None = None

    # ================================================================
    # IDENTIFIER EXTRACTION (CACHED)
    # ================================================================
    def extract_identifiers(self) -> List[str]:
        """
        Return unique column identifiers referenced by this formula.
        """
        if self._identifiers is None:
            tree = ast.parse(self.formula.expression, mode="eval")
            self._identifiers = {
                node.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Name)
            }

        return sorted(self._identifiers)

    # ================================================================
    # VALIDATION
    # ================================================================
    def missing_columns(self, schema) -> List[str]:
        """
        Return identifiers that are not present in the schema.
        """
        return [
            ident
            for ident in self.extract_identifiers()
            if not schema.columns.filter(identifier=ident).exists()
        ]

    def validate_schema_columns_exist(self, schema):
        """
        Raise ValidationError if referenced columns are missing.
        """
        missing = self.missing_columns(schema)
        if missing:
            raise ValidationError(
                f"Formula '{self.formula.identifier}' "
                f"references missing columns: {missing}"
            )

    # ================================================================
    # CONTEXT BUILDING (PURE)
    # ================================================================
    def build_context(self, holding, schema) -> Dict[str, Decimal]:
        """
        Build numeric evaluation context for a single holding.

        Rules:
            - SOURCE_USER → use stored value
            - Otherwise   → compute display value
        """
        self.validate_schema_columns_exist(schema)

        context: Dict[str, Decimal] = {}

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

            # USER OVERRIDE ALWAYS WINS
            if scv.source == SchemaColumnValue.SOURCE_USER:
                context[ident] = Decimal(str(scv.value))
                continue

            # SYSTEM / FORMULA VALUE
            value = SchemaColumnValueManager.display_for_column(
                column,
                holding,
            )
            context[ident] = Decimal(str(value))

        return context

    # ================================================================
    # CYCLE DETECTION
    # ================================================================
    def detect_cycles(self, schema, start_identifier: str):
        """
        Raise ValidationError if a formula dependency cycle exists.
        """
        self._dfs(schema, start_identifier, set())

    def _dfs(self, schema, identifier: str, visited: Set[str]):
        if identifier in visited:
            raise ValidationError(
                f"Formula dependency cycle detected involving '{identifier}'."
            )

        visited.add(identifier)

        column = schema.columns.filter(identifier=identifier).first()
        if not column or not column.formula:
            return

        resolver = FormulaDependencyResolver(column.formula)
        for dep in resolver.extract_identifiers():
            self._dfs(schema, dep, visited)
