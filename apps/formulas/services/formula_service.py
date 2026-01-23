from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils.text import slugify

from formulas.models.formula import Formula
from formulas.services.system_registry import SystemFormulaRegistry


class FormulaService:
    """
    High-level service responsible for Formula lifecycle.

    This is the ONLY place where:
    - formulas are created
    - formulas are edited
    - system/user boundaries are enforced
    """

    @staticmethod
    @transaction.atomic
    def create_user_formula(*, user, expression, identifier, title=None, decimal_places=None):
        """
        Create a user-owned formula.

        Rules:
        - Identifier is REQUIRED
        - Identifier is normalized (slugified)
        - Identifier cannot collide with system identifiers
        - Identifier must be unique per user (DB enforced)
        """

        if not identifier:
            raise ValidationError("Identifier is required.")

        normalized_identifier = slugify(identifier)

        if SystemFormulaRegistry.is_reserved(normalized_identifier):
            raise ValidationError(
                f"'{normalized_identifier}' is a reserved system formula identifier."
            )

        formula = Formula(
            owner=user.profile,
            title=title,
            identifier=identifier,
            expression=expression,
            decimal_places=decimal_places,
        )
        formula.save()
        return formula

    @staticmethod
    @transaction.atomic
    def update_formula(*, user, formula: Formula, **updates):
        """
        Update a formula.

        Rules:
        - System formulas cannot be edited
        - Users can only edit their own formulas
        - Dependencies are always recalculated automatically
        """

        FormulaService._assert_can_edit(user, formula)

        for field in ["title", "expression", "decimal_places", "identifier"]:
            if field in updates:
                setattr(formula, field, updates[field])

        formula.save()
        return formula

    @staticmethod
    @transaction.atomic
    def delete_formula(*, user, formula: Formula):
        """
        Delete a formula.

        Rules:
        - System formulas cannot be deleted
        - Users can only delete their own formulas
        """

        FormulaService._assert_can_edit(user, formula)
        formula.delete()

    @staticmethod
    def get_formula_for_user(*, user, identifier) -> Formula:
        """
        Resolve a formula for a user by identifier.

        Resolution order:
        1. User-owned formula
        2. System formula
        """

        # User-owned first
        formula = Formula.objects.filter(
            identifier=identifier,
            owner=user.profile,
        ).first()

        if formula:
            return formula

        # System fallback
        return Formula.objects.get(
            identifier=identifier,
            owner__isnull=True,
        )

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _assert_can_edit(user, formula: Formula):
        """
        Ensure the user has permission to mutate the formula.
        """

        if formula.owner is None:
            raise PermissionDenied("System formulas cannot be modified.")

        if formula.owner_id != user.profile.id:
            raise PermissionDenied("You do not own this formula.")
