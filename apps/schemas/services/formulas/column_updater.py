from django.db import transaction
from django.core.exceptions import ValidationError

from schemas.models.schema import Schema, SchemaColumn
from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.formulas.update_engine import FormulaUpdateEngine


class FormulaColumnUpdater:
    """
    Attaches an existing formula to an existing SchemaColumn.

    Responsibilities:
        ✔ Ensure all dependency columns already exist
        ✔ Do NOT auto-create dependency columns
        ✔ Create SCVs for target column
        ✔ Trigger full formula recalculation across holdings

    This service is used in UI workflows where:
        - The user picked the target column
        - The user picked the formula
        - Dependencies already exist (template or custom)
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # ============================================================
    # MAIN ENTRYPOINT
    # ============================================================
    @transaction.atomic
    def attach(self, schema: Schema, target_column: SchemaColumn):
        """
        Attach the formula to this column and trigger all downstream updates.
        """

        resolver = FormulaDependencyResolver(self.formula)

        # --------------------------------------------------------
        # 1. Dependencies must exist already
        # --------------------------------------------------------
        resolver.validate_schema_columns_exist(schema)

        # --------------------------------------------------------
        # 2. Attach formula to schema column
        # --------------------------------------------------------
        target_column.formula = self.formula
        target_column.source = "formula"
        target_column.source_field = None
        target_column.save(update_fields=["formula", "source", "source_field"])

        # --------------------------------------------------------
        # 3. Create SCVs for all holdings
        # --------------------------------------------------------
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )
        for account in accounts:
            for holding in account.holdings.all():
                SchemaColumnValueManager.get_or_create(holding, target_column)

        # --------------------------------------------------------
        # 4. Recompute formula results using UpdateEngine
        # --------------------------------------------------------
        for account in accounts:
            for holding in account.holdings.all():

                engine = FormulaUpdateEngine(holding, schema)
                engine.update_dependent_formulas(target_column.identifier)
