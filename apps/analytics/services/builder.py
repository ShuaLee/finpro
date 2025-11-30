from dataclasses import dataclass

from django.db import transaction

from analytics.models.analytics import Analytic


@dataclass
class AnalyticDefinition:
    """
    A pure data definition used to create a new Analytic.
    """
    name: str
    label: str
    description: str | None
    dimension_name: str
    dimension_label: str
    dimension_description: str | None
    dimension_identifier: str   # SCV identifier for grouping (string)
    value_identifier: str       # SCV identifier for dollar value (decimal)


class AnalyticBuilder:
    """
    Handles creation of analytics with full schema compatibility:
      - Creates Analytic + AnalyticDimension
      - Validates SCV identifiers
      - Ensures SchemaColumns exist (or creates custom ones)
      - Ensures safety across account_types in the user's portfolio
    """

    def __init__(self, profile):
        self.profile = profile
        self.portfolio = profile.portfolio

    # ================================================================
    # Main entry
    # ================================================================
    @transaction.atomic
    def create(self, definition: AnalyticDefinition) -> Analytic:
        """
        Main entrypoint.

        Steps:
          1. Create Analytic
          2. Create Dimension
          3. Ensure SchemaColumns exist for each identifier
          4. Return Analytic instance
        """

        analytic = Analytic.objects.create(
            profile=self.profile,
            name=definition.name,
            label=definition.label,
            description=definition.description,
            is_active=True
        )

        dimension = AnalyticDefinition.objects.create(
            analytic=analytic,
            name=definition.dimension_name,
            label=definition.dimension_label,
            description=definition.dimension_description,
            is_active=True
        )

        # Ensure all schemas have the required identifier columns
        self._ensure_schema_column_exists(
            definition.dimension_identifier, data_type="string")
        self._ensure_schema_column_exists(
            definition.value_identifier, data_type="decimal")

        return analytic
