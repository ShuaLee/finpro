from django.db import transaction
from decimal import Decimal
from collections import defaultdict

from analytics.models.analytics import (
    Analytic,
    AnalyticDimension,
    AnalyticDimensionValue,
)
from schemas.models.schema import SchemaColumnValue, SchemaColumn
from schemas.services.schema_column_value_manager import SchemaColumnValueManager


class AnalyticsEngine:
    """
    Computes analytics for a given Analytic.

    Workflow:
        1. For each dimension:
            - Ensure grouping/value columns exist in all schemas
            - Read SCVs from every holding
            - Group + sum
            - Calculate percentages
            - Write AnalyticDimensionValue rows
    """

    def __init__(self, analytic: Analytic):
        self.analytic = analytic
        self.profile = analytic.portfolio.profile
        self.portfolio = analytic.portfolio

    # ======================================================================
    # MAIN ENTRY
    # ======================================================================
    @transaction.atomic
    def compute(self):
        """
        Computes the entire analytic and returns a Python dict for admin.
        All previous AnalyticDimensionValues are deleted.
        """

        # Wipe previous computed values
        AnalyticDimensionValue.objects.filter(
            dimension__analytic=self.analytic
        ).delete()

        results = {}

        for dimension in self.analytic.dimensions.filter(is_active=True):
            results[dimension.name] = self._compute_dimension(dimension)

        return results

    # ======================================================================
    # SINGLE DIMENSION COMPUTATION
    # ======================================================================
    def _compute_dimension(self, dimension: AnalyticDimension):
        """
        Compute SUM + percentage for one dimension.
        """

        group_identifier = dimension.source_identifier           # e.g. 'country'
        # e.g. 'current_value_profile_fx'
        value_identifier = self.analytic.value_identifier

        # Make sure all schemas contain the SCV columns we depend on
        self._ensure_schema_column(group_identifier, data_type="string")
        self._ensure_schema_column(value_identifier, data_type="decimal")

        totals = defaultdict(Decimal)

        # All holdings for this portfolio
        holdings = [
            h
            for acct in self.portfolio.accounts.all()
            for h in acct.holdings.all()
        ]

        for holding in holdings:
            group_value = self._get_scv_text(holding, group_identifier)
            numeric_value = self._get_scv_decimal(holding, value_identifier)

            if not group_value:
                group_value = "Unknown"

            totals[group_value] += numeric_value

        grand_total = sum(totals.values()) or Decimal("1")

        # Build DB rows
        rows = []
        for grp, total in totals.items():
            pct = (total / grand_total) if grand_total else Decimal("0")

            rows.append(
                AnalyticDimensionValue(
                    dimension=dimension,
                    dimension_value=grp,
                    total_value=total,
                    percentage=pct,
                )
            )

        AnalyticDimensionValue.objects.bulk_create(rows)
        return rows

    # ======================================================================
    # SCV HELPERS
    # ======================================================================
    def _get_scv_text(self, holding, identifier):
        scv = SchemaColumnValue.objects.filter(
            holding=holding,
            column__identifier=identifier
        ).first()

        return scv.value if scv else None

    def _get_scv_decimal(self, holding, identifier):
        val = self._get_scv_text(holding, identifier)
        try:
            return Decimal(str(val or "0"))
        except:
            return Decimal("0")

    # ======================================================================
    # SCHEMA COLUMN ENSURE
    # ======================================================================
    def _ensure_schema_column(self, identifier: str, data_type: str):
        """
        Ensures EVERY schema in the portfolio contains the column with the given identifier.

        Rules:
            - If the column exists → verify matching data_type
            - If the identifier exists in the SchemaTemplate → use template definition
            - Otherwise → create custom column
            - Always refresh SCVs for all holdings
        """

        schemas = self.portfolio.schemas.all()

        for schema in schemas:
            existing = schema.columns.filter(identifier=identifier).first()

            if existing:
                if existing.data_type != data_type:
                    raise ValueError(
                        f"SchemaColumn '{identifier}' in {schema.account_type} "
                        f"is {existing.data_type}, expected {data_type}."
                    )
                continue

            # Try template match
            from schemas.models.template import SchemaTemplateColumn

            template_col = (
                SchemaTemplateColumn.objects
                .filter(template__account_type=schema.account_type,
                        identifier=identifier)
                .first()
            )

            if template_col:
                # Create from template
                column = SchemaColumn.objects.create(
                    schema=schema,
                    title=template_col.title,
                    identifier=identifier,
                    data_type=template_col.data_type,
                    source=template_col.source,
                    source_field=template_col.source_field,
                    formula=template_col.formula,
                    is_editable=template_col.is_editable,
                    is_deletable=template_col.is_deletable,
                    is_system=template_col.is_system,
                    display_order=schema.columns.count() + 1,
                )

                from schemas.services.schema_constraint_manager import SchemaConstraintManager
                SchemaConstraintManager.create_from_master(
                    column,
                    overrides=template_col.constraints or {}
                )
            else:
                # Create custom column
                column = SchemaColumn.objects.create(
                    schema=schema,
                    title=identifier.replace("_", " ").title(),
                    identifier=identifier,
                    data_type=data_type,
                    source="custom",
                    source_field=None,
                    is_editable=True,
                    is_deletable=True,
                    is_system=False,
                    display_order=schema.columns.count() + 1,
                )

                # Add safe default constraints
                from schemas.services.schema_constraint_manager import SchemaConstraintManager
                SchemaConstraintManager.create_from_master(
                    column,
                    overrides={
                        "max_length": 255 if data_type == "string" else None,
                        "decimal_places": 2 if data_type == "decimal" else None,
                    }
                )

            # SCVs must exist after column creation
            from schemas.services.schema_manager import SchemaManager
            for acct in self.portfolio.accounts.filter(account_type=schema.account_type):
                SchemaManager(schema).ensure_for_all_holdings(acct)
