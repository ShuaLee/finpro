from typing import Any

from schemas.models.schema import SchemaColumnValue
from schemas.models.schema import SchemaColumn
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class SchemaColumnEvaluator:
    """
    Unified evaluation service for ANY SchemaColumn.

    Thin wrapper around SCV + SCV Manager.
    """

    def __init__(self, holding, column: SchemaColumn):
        self.holding = holding
        self.column = column

    # =======================================================
    # PUBLIC API
    # =======================================================
    def evaluate(self) -> Any:
        """
        Return final formatted value.
        """

        scv_mgr = SchemaColumnValueManager.get_or_create(
            self.holding,
            self.column,
        )
        scv = scv_mgr.scv

        # ---------------------------------------------------
        # 1. USER OVERRIDE ALWAYS WINS
        # ---------------------------------------------------
        if scv.source == SchemaColumnValue.SOURCE_USER:
            return scv.value

        # ---------------------------------------------------
        # 2. EVERYTHING ELSE → SCV MANAGER
        # ---------------------------------------------------
        return SchemaColumnValueManager.display_for_column(
            self.column,
            self.holding,
        )
