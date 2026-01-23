from django.core.exceptions import ValidationError
from django.db import transaction

from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.scv_refresh_service import SCVRefreshService


class FormulaBuilder:
    """
    Attaches USER-defined formulas to SchemaColumns.

    Rules:
    - System formulas are forbidden here
    - All dependency columns must already exist
    - No schema mutation beyond attaching the formula
    """

    def __init__(self, formula):
        self.formula = formula

    @transaction.atomic
    def attach_to_column(self, schema, target_column):
        # -------------------------------------------------
        # 1. Guard: system formulas not allowed
        # -------------------------------------------------
        if self.formula.is_system:
            raise ValidationError(
                "System formulas must be added via schema expansion."
            )

        resolver = FormulaDependencyResolver(self.formula)

        # -------------------------------------------------
        # 2. Validate dependencies exist
        # -------------------------------------------------
        resolver.validate_schema_columns_exist(schema)

        # -------------------------------------------------
        # 3. Detect cycles
        # -------------------------------------------------
        resolver.detect_cycles(schema, target_column.identifier)

        # -------------------------------------------------
        # 4. Attach formula
        # -------------------------------------------------
        target_column.formula = self.formula
        target_column.source = "formula"
        target_column.source_field = None
        target_column.save(update_fields=["formula", "source", "source_field"])

        # -------------------------------------------------
        # 5. Ensure SCVs exist (target column only)
        # -------------------------------------------------
        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )

        for account in accounts:
            for holding in account.holdings.all():
                SchemaColumnValueManager.get_or_create(
                    holding,
                    target_column,
                )

        # -------------------------------------------------
        # 6. Trigger recompute centrally
        # -------------------------------------------------
        SCVRefreshService.schema_changed(schema)
