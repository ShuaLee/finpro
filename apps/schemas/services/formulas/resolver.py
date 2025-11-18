from schemas.models.formula import Formula

from typing import List

import ast


class FormulaDependencyResolver:
    """
    Parses formula expressions, extracts identifiers,
    ensures SchemaColumns and SCVs exist, and builds raw-value context
    for formula evaluation.
    """

    NUMERIC_TYPES = {"decimal", "integer"}

    def __init__(self, formula: Formula):
        self.formula = formula

    # =====================================================================
    # PUBLIC API
    # =====================================================================
    def extract_identifiers(self) -> List[str]:
        """
        Parse the formula expression and return a list of identifiers
        referenced in the formula.
        """
        tree = ast.parse(self.formula.expression, mode="eval")
        visitor = _IdentifierVisitor()
        visitor.visit(tree)
        return visitor.identifiers

# =====================================================================
# AST Visitor to extract identifiers
# =====================================================================


class _IdentifierVisitor(ast.NodeVisitor):
    def __init__(self):
        self.identifiers: List[str] = []

    def visit_name(self, node: ast.Name):
        self.identifiers.append(node.id)
