from django.db import transaction
from django.core.exceptions import ValidationError

from schemas.models import MasterConstraint
from schemas.models.constraints import SchemaConstraint
from schemas.services.scv_refresh_service import SCVRefreshService


class SchemaConstraintEditService:
    """
    Canonical entry point for mutating SchemaConstraints.
    """

    @staticmethod
    @transaction.atomic
    def update_constraint(
        *,
        constraint: SchemaConstraint,
        user=None,
        changed_fields: list[str],
        updates: dict,
    ) -> SchemaConstraint:

        previous = SchemaConstraint.objects.get(pk=constraint.pk)

        master = MasterConstraint.objects.get(
            name=constraint.name,
            applies_to=constraint.applies_to,
        )

        # --------------------------------------------------
        # 1️⃣ Apply updates ONLY ONCE (admin already mutated obj)
        # --------------------------------------------------
        # DO NOT re-set fields here

        constraint.full_clean()

        # --------------------------------------------------
        # 2️⃣ Detect editable → non-editable transition
        # --------------------------------------------------
        if (
            "is_editable" in changed_fields
            and previous.is_editable
            and not constraint.is_editable
        ):
            SchemaConstraintEditService._reset_to_master_default(
                constraint, master
            )

        constraint.save()

        # --------------------------------------------------
        # 3️⃣ Recompute SCVs
        # --------------------------------------------------
        SCVRefreshService.schema_changed(
            constraint.column.schema
        )

        return constraint

    # ======================================================
    # INTERNAL HELPERS
    # ======================================================

    @staticmethod
    def _reset_to_master_default(
        constraint: SchemaConstraint,
        master: MasterConstraint,
    ):
        """
        Force constraint back to system default.
        """

        default = master.default_value()

        if constraint.applies_to in ("decimal", "percent"):
            constraint.value_decimal = default
            constraint.min_decimal = master.min_decimal
            constraint.max_decimal = master.max_decimal

        elif constraint.applies_to == "string":
            constraint.value_string = default

        elif constraint.applies_to == "boolean":
            constraint.value_boolean = default

        elif constraint.applies_to == "date":
            constraint.value_date = default
            constraint.min_date = master.min_date
            constraint.max_date = master.max_date
