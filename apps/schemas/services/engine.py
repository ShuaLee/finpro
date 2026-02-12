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
