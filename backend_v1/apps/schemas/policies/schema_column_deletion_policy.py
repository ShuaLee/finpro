from django.core.exceptions import ValidationError

from schemas.models.schema_column import SchemaColumn
from schemas.services.queries import SchemaQueryService


class SchemaColumnDeletionPolicy:
    @staticmethod
    def assert_deletable(*, column: SchemaColumn) -> None:
        SchemaColumnDeletionPolicy._assert_flag_allows(column)
        SchemaColumnDeletionPolicy._assert_no_formula_dependents(column)

    @staticmethod
    def _assert_flag_allows(column: SchemaColumn) -> None:
        if not column.is_deletable:
            raise ValidationError(
                f"SchemaColumn '{column.identifier}' is not deletable "
                f"(system or protected column)."
            )

    @staticmethod
    def _assert_no_formula_dependents(column):
        dependents = SchemaQueryService.dependents_of(
            schema=column.schema,
            identifier=column.identifier,
        )
        if dependents:
            raise ValidationError(
                f"Cannot delete column '{column.identifier}'. "
                f"Dependent columns: {', '.join(sorted(dependents))}"
            )
