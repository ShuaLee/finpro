from django.core.exceptions import ValidationError

from schemas.models.schema_column import SchemaColumn
from schemas.services.schema_column_dependency_graph import SchemaColumnDependencyGraph


class SchemaColumnDeletionPolicy:
    """
    Authoritative rules for whether a SchemaColumn may be deleted.

    This class MUST be the single source of truth.
    """

    # ==========================================================
    # PUBLIC API
    # ==========================================================
    @staticmethod
    def assert_deletable(*, column: SchemaColumn) -> None:
        """
        Raise ValidationError if the column cannot be deleted.
        """
        SchemaColumnDeletionPolicy._assert_flag_allows(column)
        SchemaColumnDeletionPolicy._assert_no_formula_dependents(column)

    # ==========================================================
    # RULES
    # ==========================================================
    @staticmethod
    def _assert_flag_allows(column: SchemaColumn) -> None:
        if not column.is_deletable:
            raise ValidationError(
                f"SchemaColumn '{column.identifier}' is not deletable "
                f"(system or protected column)."
            )

    @staticmethod
    def _assert_no_formula_dependents(column):
        dependents = SchemaColumnDependencyGraph.dependents_of(
            schema=column.schema,
            identifier=column.identifier,
        )

        if dependents:
            raise ValidationError(
                f"Cannot delete column '{column.identifier}'. "
                f"Dependent columns: {', '.join(sorted(dependents))}"
            )