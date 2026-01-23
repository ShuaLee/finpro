from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q

from formulas.models.formula_definition import FormulaDefinition, DependencyPolicy
from formulas.models.formula import Formula
from formulas.services.system_registry import SystemFormulaRegistry


class FormulaDefinitionService:
    """
    High-level service responsible for FormulaDefinition lifecycle
    and resolution.

    This is the ONLY place where:
    - formula definitions are created
    - system vs user rules are enforced
    - resolution with fallback occurs
    """

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def create_user_definition(
        *,
        user,
        identifier,
        asset_type,
        formula: Formula,
        name,
        description="",
        dependency_policy=DependencyPolicy.STRICT,
    ):
        """
        Create a user-owned FormulaDefinition.

        Rules:
        - Identifier is required and explicit
        - Identifier cannot be system-reserved
        - User must own the formula
        - Definition is scoped to (identifier, asset_type, owner)
        """

        if not identifier:
            raise ValidationError("Identifier is required.")

        if SystemFormulaRegistry.is_reserved(identifier):
            raise ValidationError(
                f"'{identifier}' is a reserved system formula identifier."
            )

        # User must own the formula
        if formula.owner_id != user.profile.id:
            raise PermissionDenied("You do not own the referenced formula.")

        definition = FormulaDefinition(
            owner=user.profile,
            identifier=identifier,
            name=name,
            description=description,
            asset_type=asset_type,
            formula=formula,
            dependency_policy=dependency_policy,
            is_system=False,
        )
        definition.save()
        return definition

    # ------------------------------------------------------------------
    # Update / delete
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def update_definition(*, user, definition: FormulaDefinition, **updates):
        """
        Update a FormulaDefinition.

        Rules:
        - System definitions cannot be edited
        - Users can only edit their own definitions
        """

        FormulaDefinitionService._assert_can_edit(user, definition)

        for field in [
            "name",
            "description",
            "formula",
            "dependency_policy",
        ]:
            if field in updates:
                setattr(definition, field, updates[field])

        definition.save()
        return definition

    @staticmethod
    @transaction.atomic
    def delete_definition(*, user, definition: FormulaDefinition):
        """
        Delete a FormulaDefinition.

        Rules:
        - System definitions cannot be deleted
        - Users can only delete their own definitions
        """

        FormulaDefinitionService._assert_can_edit(user, definition)
        definition.delete()

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    @staticmethod
    def resolve(*, identifier, asset_type, user=None) -> FormulaDefinition:
        """
        Resolve the effective FormulaDefinition.

        Resolution order:
        1. User-owned definition (if user provided)
        2. System definition (owner IS NULL)

        Raises ValidationError if no definition exists.
        """

        qs = FormulaDefinition.objects.filter(
            identifier=identifier,
            asset_type=asset_type,
        )

        if user:
            qs = qs.filter(
                Q(owner=user.profile) | Q(owner__isnull=True)
            ).order_by(
                Q(owner=user.profile).desc()
            )
        else:
            qs = qs.filter(owner__isnull=True)

        definition = qs.first()

        if not definition:
            raise ValidationError(
                f"No formula definition found for '{identifier}' "
                f"and asset type '{asset_type}'."
            )

        return definition

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @staticmethod
    def list_available(*, asset_type, user=None):
        """
        List available FormulaDefinitions for an asset type.

        Includes:
        - user-owned definitions
        - system definitions
        """

        qs = FormulaDefinition.objects.filter(
            asset_type=asset_type,
        )

        if user:
            return qs.filter(
                Q(owner=user.profile) | Q(owner__isnull=True)
            )

        return qs.filter(owner__isnull=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _assert_can_edit(user, definition: FormulaDefinition):
        """
        Ensure the user has permission to mutate the definition.
        """
        if definition.owner is None:
            raise PermissionDenied(
                "System formula definitions cannot be modified.")

        if definition.owner_id != user.profile.id:
            raise PermissionDenied("You do not own this formula definition.")
