from django.db import transaction

from schemas.models.schema import Schema, SchemaColumn
from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.formulas.update_engine import FormulaUpdateEngine


class FormulaColumnUpdater:
    """
    Attaches a formula to a SchemaColumn and ensures that:

      ✔ referenced columns already exist (NO auto-create)
      ✔ SCVs exist for all holdings
      ✔ initial value is computed using SCVs
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # ============================================================
    # MAIN ENTRYPOINT
    # ============================================================
    @transaction.atomic
    def attach(self, schema: Schema, target_column: SchemaColumn):
        # --------------------------------------------------------
        # 1. Validate dependencies exist
        # --------------------------------------------------------
        resolver = FormulaDependencyResolver(self.formula)
        resolver.validate_schema_columns_exist(schema)

        # --------------------------------------------------------
        # 2. Attach formula to this column
        # --------------------------------------------------------
        target_column.formula = self.formula
        target_column.source = "formula"
        target_column.source_field = None
        target_column.save(update_fields=["formula", "source", "source_field"])

        # --------------------------------------------------------
        # 3. Ensure SCVs for all holdings
        # --------------------------------------------------------
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )

        for account in accounts:
            for holding in account.holdings.all():
                SchemaColumnValueManager.get_or_create(holding, target_column)

        # --------------------------------------------------------
        # 4. Compute initial results
        # --------------------------------------------------------
        for account in accounts:
            for holding in account.holdings.all():
                engine = FormulaUpdateEngine(holding, schema)
                engine.update_dependent_formulas(target_column.identifier)
