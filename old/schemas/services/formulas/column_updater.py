from django.db import transaction
from django.core.exceptions import ValidationError

from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.formulas.update_engine import FormulaUpdateEngine


class FormulaColumnUpdater:
    """
    Attaches an existing formula to an existing SchemaColumn.

    Responsibilities:
        ✔ Ensure dependency columns already exist (no auto-create)
        ✔ Detect cycles before attaching
        ✔ Attach formula cleanly
        ✔ Ensure SCVs exist for all holdings
        ✔ Trigger formula recalculation for all dependent formulas
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    @transaction.atomic
    def attach(self, schema, target_column):
        """
        Attach a formula to an existing SchemaColumn.
        Does NOT auto-create dependency columns.
        """
        if not self.formula.is_system:
            raise ValidationError(
                "FormulaColumnUpdater is only for system formulas."
            )

        # Lazy imports (prevents circular import loops)
        from schemas.models.schema import SchemaColumn

        resolver = FormulaDependencyResolver(self.formula)

        # --------------------------------------------------------
        # 1. Validate dependency columns exist
        # --------------------------------------------------------
        resolver.validate_schema_columns_exist(schema)

        # --------------------------------------------------------
        # 2. Detect cycles BEFORE applying formula
        # --------------------------------------------------------
        resolver.detect_cycles(schema, target_column.identifier)

        # --------------------------------------------------------
        # 3. Attach formula to the SchemaColumn
        # --------------------------------------------------------
        target_column.formula = self.formula
        target_column.source = "formula"
        target_column.source_field = None
        target_column.save(update_fields=["formula", "source", "source_field"])

        # --------------------------------------------------------
        # 4. Ensure SCVs exist for all holdings
        # --------------------------------------------------------
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )
        for account in accounts:
            for holding in account.holdings.all():
                SchemaColumnValueManager.get_or_create(holding, target_column)

        # --------------------------------------------------------
        # 5. Run full recomputation through the UpdateEngine
        # --------------------------------------------------------
        for account in accounts:
            for holding in account.holdings.all():
                engine = FormulaUpdateEngine(holding, schema)
                engine.update_dependent_formulas(target_column.identifier)
