from django.db import transaction

from analytics.models.analytics import Analytic, AnalyticDimension, AnalyticDimensionValue
from schemas.models.schema import SchemaColumn, SchemaColumnValue
from schemas.services.schema_manager import SchemaManager

from collections import defaultdict
from decimal import Decimal


class AnalyticsEngine:
    """
    Computes analytics for a given Analytic.
    1. Ensures all schemas contain required dimension columns
    2. Reads SCV values for each holding
    3. Aggregates totals
    4. Writes AnalyticDimensionValues
    """

    def __init__(self, analytic: Analytic):
        self.analytic = analytic
        self.profile = analytic.profile
        self.portfolio = analytic.profile.portfolio

    # ======================================================================
    # MAIN ENTRY
    # ======================================================================
    @transaction.atomic
    def compute(self):
        """
        Compute all dimensions of this analytic and write dimension values.
        """
        # Clear old values
        AnalyticDimensionValue.objects.filter(
            dimension__analytic=self.analytic
        ).delete()

        results = {}

        for dimension in self.analytic.dimensions.filter(is_active=True):
            result = self._compute_dimension(dimension)
            results[dimension.name] = result

        return results

    # ======================================================================
    # SINGLE DIMENSION COMPUTATION
    # ======================================================================
    def _compute_dimension(self, dimension: AnalyticDimension):
        """
        Compute a single dimension (e.g., "country").
        """
        dim_identifier = dimension.source_identifier
        val_identifier = self.analytic.value_identifier

        # Ensure required columns exists for ALL schemas
        self._ensure_schema_column(dim_identifier)
        self._ensure_schema_column(val_identifier)

        # For summing value buckets
        totals = defaultdict(Decimal)

        # All holdings in the user's portfolio
        accounts = self.portfolio.accounts.all()
        holdings = [
            h for a in accounts for h in a.holdings.all()
        ]

        # Compute dimension -> total_value mapping
        for holding in holdings:
            dim_value = self._get_scv_value(holding, dim_identifier)
            val_value = self._get_numeric_scv_value(holding, val_identifier)

            if dim_value is None:
                dim_value = "Unknown"

            totals[dim_value] += val_value

        grand_total = sum(totals.values()) or Decimal("1")

        # Save rows
        dim_values = []
        for bucket, total in totals.items():
            pct = (total / grand_total) if grand_total else Decimal("0")

            dim_values.append(
                AnalyticDimensionValue(
                    dimension=dimension,
                    dimension_value=bucket,
                    total_value=total
                )
            )

        AnalyticDimensionValue.objects.bulk_create(dim_values)
        return dim_values

    # ======================================================================
    # SCV ACCESS HELPERS
    # ======================================================================
    def _get_scv_value(self, holding, identifier):
        """
        Returns SCV.value for the given identifier.
        """
        scv = SchemaColumnValue.objects.filter(
            holding=holding,
            column__identifier=identifier
        ).first()

        return scv.value if scv else None

    def _get_numeric_scv_value(self, holding, identifier):
        """
        Fetch a decimal SCV value safely.
        """
        val = self._get_scv_value(holding, identifier)
        try:
            return Decimal(str(val or "0"))
        except:
            return Decimal("0")

    # ======================================================================
    # SCHEMA COLUMN ENSURE LOGIC
    # ======================================================================
    def _ensure_schema_column(self, identifier):
        """
        Ensure that *every schema* in the user portfolio has a column with
        the given identifier.

        Rules:
            - If SchemaTemplate defines it → use template definition
            - Otherwise create a custom string column
            - SCVs automatically populated
        """
        schemas = self.portfolio.schemas.all()

        for schema in schemas:
            col = schema.columns.filter(identifier=identifier).first()
            if col:
                continue

            # Template lookup (if exists)
            from schemas.models.template import SchemaTemplate, SchemaTemplateColumn

            template = SchemaTemplate.objects.filter(
                account_type=schema.account_type
            ).first()

            template_col = None
            if template:
                template_col = template.columns.filter(
                    identifier=identifier
                ).first()

            # If defined in template -> use template definition
            if template_col:
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
                # Otherwise create a CUSTOM column
                column = SchemaColumn.objects.create(
                    schema=schema,
                    title=identifier.replace("_", " ").title(),
                    identifier=identifier,
                    data_type="string",
                    source="custom",
                    source_field=None,
                    is_editable=True,
                    is_deletable=True,
                    is_system=False,
                    display_order=schema.columns.count() + 1,
                )

                from schemas.services.schema_constraint_manager import SchemaConstraintManager
                SchemaConstraintManager.create_from_master(column, overrides={
                    "max_length": 255
                })

                # Create SCVs for all holdings
                SchemaManager(schema).ensure_for_all_holdings(
                    schema.portfolio.accounts.get(
                        account_type=schema.account_type
                    )
                )
