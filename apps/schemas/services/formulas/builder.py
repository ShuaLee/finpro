from django.core.exceptions import ValidationError
from django.db import transaction

from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.formulas.update_engine import FormulaUpdateEngine


class FormulaBuilder:
    """
    Auto-create dependency columns if missing.
    """

    def __init__(self, formula):
        self.formula = formula

    @transaction.atomic
    def attach_to_column(self, schema, target_column):

        resolver = FormulaDependencyResolver(self.formula)

        dependency_columns = []

        for ident in resolver.extract_identifiers():
            col = schema.columns.filter(identifier=ident).first()
            if col:
                dependency_columns.append(col)
                continue

            # Auto-create NON-formula dependency column
            from schemas.models.schema import SchemaColumn

            col = SchemaColumn.objects.create(
                schema=schema,
                title=ident.replace("_", " ").title(),
                identifier=ident,
                data_type="decimal",
                source="custom",
                is_editable=False,
                is_deletable=True,
                is_system=False,
                display_order=schema.columns.count() + 1,
            )
            dependency_columns.append(col)

        resolver.detect_cycles(schema, target_column.identifier)

        target_column.formula = self.formula
        target_column.source = "formula"
        target_column.source_field = None
        target_column.save(update_fields=["formula", "source", "source_field"])

        accounts = schema.portfolio.accounts.filter(
            account_type=schema.account_type
        )

        for account in accounts:
            for holding in account.holdings.all():
                for col in [target_column] + dependency_columns:
                    SchemaColumnValueManager.get_or_create(holding, col)

                FormulaUpdateEngine(holding, schema).update_dependent_formulas(
                    target_column.identifier
                )
