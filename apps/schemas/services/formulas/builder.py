from django.db import transaction

from schemas.models.formula import Formula
from schemas.models.schema import Schema, SchemaColumn

from typing import List


class FormulaBuilder:
    """
    Responsible for attaching a formula to a schema column AND ensuring:

      ✔ All dependencies exist as SchemaColumns
      ✔ Missing ones are created as computed columns
      ✔ Every holding gets SCVs for those columns
      ✔ Initial SCV values are populated

    Absolutely NEVER mutates Holdings.
    SCVs only.
    """

    def __init__(self, formula: Formula):
        self.formula = formula

    # =====================================================================
    # MAIN ENTRY POINT
    # =====================================================================
    @transaction.atomic
    def attach_to_column(self, schema: Schema, target_column: SchemaColumn):
        """
        Assign this formula to the target SchemaColumn, build dependencies,
        and populate SCVs.
        """
        # -----------------------------
        # 1. Create or verify dependency columns
        # -----------------------------
        dep_columns = self._ensure_dependency_columns(schema)

        # -----------------------------
        # 2. Attach the formula to target column
        # -----------------------------
        target_column.formula = self.formula
        target_column.source = None
        target_column.source_field = None
        target_column.save(update_fields=["formula", "source", "source_field"])

        # -----------------------------
        # 3. Ensure SCVs exist for all dependency columns + target
        # -----------------------------
        self._ensure_scvs_for_schema(schema, [target_column] + dep_columns)

        # -----------------------------
        # 4. Compute initial SCV values
        # -----------------------------
        self._initial_compute(schema, target_column)

    # =====================================================================
    # DEPENDENCY COLUMN CREATION
    # =====================================================================

    def _ensure_dependency_columns(self, schema: Schema) -> List[SchemaColumn]:
        """
        Ensure all identifiers referenced in the formula expression are
        present as SchemaColumns. Missing ones become computed numeric columns.
        """
        identifiers = self._extract_identifiers()
        dep_columns = []

        for ident in identifiers:
            col = schema.columns.filter(identifier=ident).first()

            if not col:
                col = SchemaColumn.objects.create(
                    schema=schema,
                    title=ident.replace("_", " ").title(),
                    identifier=ident,
                    data_type="decimal",
                    source=None,
                    source_field=None,
                    is_editable=False,
                    is_deletable=True,
                    is_system=False,
                    display_order=schema.columns.count() + 1,
                )

            dep_columns.append(col)

        return dep_columns

    # =====================================================================
    # SCV CREATION
    # =====================================================================
    def _ensure_scvs_for_schema(self, schema: Schema, columns: List[SchemaColumn]):
        """
        Ensure SCVs exist for all holdings for all columns.
        """
