from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction

from analytics.models.analytics import Analytic, AnalyticDimension
from schemas.services.schema_column_factory import SchemaColumnFactory
from schemas.models.schema import Schema


@dataclass
class AnalyticDefinition:
    """
    Pure data container defining a new analytic.
    """
    name: str
    label: str
    description: str | None
    dimension_name: str
    dimension_label: str
    dimension_description: str | None

    # SCV identifiers
    dimension_identifier: str      # string SCV used for grouping
    value_identifier: str          # decimal SCV used for summing


class AnalyticBuilder:
    """
    Creates analytics in a way that is fully schema-safe:

    - Creates the Analytic and its Dimension
    - Ensures SchemaColumns exist for the dimension/value
    - Uses SchemaColumnFactory to create missing columns uniformly
    """

    def __init__(self, profile):
        self.profile = profile
        self.portfolio = profile.portfolio

    # ==============================================================
    @transaction.atomic
    def create(self, definition: AnalyticDefinition) -> Analytic:
        """
        Main entrypoint for creating an analytic.
        """
        # 1. Create Analytic
        analytic = Analytic.objects.create(
            profile=self.profile,
            name=definition.name,
            label=definition.label,
            description=definition.description,
            is_active=True,
        )

        # 2. Create Dimension
        AnalyticDimension.objects.create(
            analytic=analytic,
            name=definition.dimension_name,
            label=definition.dimension_label,
            description=definition.dimension_description,
            is_active=True,
        )

        # 3. Ensure necessary schema columns
        self._ensure_column_for_all_schemas(
            identifier=definition.dimension_identifier,
            title=definition.dimension_label,
            data_type="string",
        )

        self._ensure_column_for_all_schemas(
            identifier=definition.value_identifier,
            title=definition.value_identifier.replace("_", " ").title(),
            data_type="decimal",
        )

        return analytic

    # ==============================================================
    def _ensure_column_for_all_schemas(self, identifier: str, title: str, data_type: str):
        """
        Ensures that every Schema in the portfolio has the given column.
        Uses SchemaColumnFactory to create custom columns when needed.
        """
        schemas = Schema.objects.filter(portfolio=self.portfolio)

        for schema in schemas:
            existing = schema.columns.filter(identifier=identifier).first()

            if existing:
                # Validate consistent data type
                if existing.data_type != data_type:
                    raise ValidationError(
                        f"Column '{identifier}' exists in schema {schema.account_type} "
                        f"but has data_type={existing.data_type}, expected {data_type}."
                    )
                continue

            # Column missing → create it
            SchemaColumnFactory.ensure_column(
                schema=schema,
                identifier=identifier,
                title=title,
                data_type=data_type,
            )
