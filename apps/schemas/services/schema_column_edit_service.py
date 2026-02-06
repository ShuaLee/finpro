from django.db import transaction

from schemas.models import SchemaColumn, SchemaColumnValue
from schemas.services.scv_refresh_service import SCVRefreshService


class SchemaColumnEditService:
    """
    Canonical entry point for mutating SchemaColumns.
    """

    @staticmethod
    @transaction.atomic
    def update_column(*, column: SchemaColumn, changed_fields: list[str]):
        """
        Handle column-level lifecycle changes.
        """

        # --------------------------------------------------
        # Editable → Non-editable
        # --------------------------------------------------
        if "is_editable" in changed_fields and not column.is_editable:
            SchemaColumnEditService._revoke_user_overrides(column)

        # --------------------------------------------------
        # Recompute schema
        # --------------------------------------------------
        SCVRefreshService.schema_changed(column.schema)

        return column

    # ======================================================
    # INTERNALS
    # ======================================================

    @staticmethod
    def _revoke_user_overrides(column: SchemaColumn):
        """
        Remove ALL user overrides for this column.
        """

        SchemaColumnValue.objects.filter(
            column=column,
            source=SchemaColumnValue.Source.USER,
        ).update(
            value=None,
            source=SchemaColumnValue.Source.SYSTEM,
        )
