"""
users.services
~~~~~~~~~~~~~~
Contains service functions that encapsulate domain logic related to users.
These functions help keep views thin by handling business processes separately.
"""

from rest_framework.exceptions import ValidationError
from users.models import Profile
from portfolios.models.portfolio import Portfolio
from subscriptions.models import Plan, AccountType


def bootstrap_user_profile(user):
    """
    Initializes essential related objects for a new user.

    Initialize Profile for a new user with:
        Default Free plan
        Default AccountType: Individual Investor

    Args:
        user (User): The newly created user.
        country (str): Country code (ISO alpha-2).
        preferred_currency (str): Currency code (ISO alpha-3).

    Returns:
        Profile: The created or existing Profile instance.

    Raises:
        ValidationError: If the default Free plan does not exist.
    """
    profile, created = Profile.objects.get_or_create(user=user)

    # Assign Free plan if none exists
    if not profile.plan:
        free_plan = Plan.objects.filter(slug="free").first()
        if not free_plan:
            raise ValidationError(
                {"detail": "Default Free plan not found. Please initialize plans."})
        profile.plan = free_plan

    # Assign Individual Investor account type
    if not profile.account_type:
        individual_type = AccountType.objects.filter(slug="individual").first()
        if not individual_type:
            raise ValidationError({"detail": "Default AccountType 'individual' not found."})
        profile.account_type = individual_type

    profile.save(update_fields=["plan", "account_type"])

    return profile


def validate_required_profile_fields(data, partial=False):
    """
    Ensures that required profile fields are provided when updating profile.

    Args:
        data (dict): Incoming validated data from serializer.
        partial (bool): Whether this is a partial update (PATCH).

    Raises:
        ValidationError: If required fields are missing.
    """
    if not partial:
        missing = []
        if not data.get('country'):
            missing.append('country')
        if not data.get('preferred_currency'):
            missing.append('preferred_currency')
        if missing:
            raise ValidationError(
                {"detail": f"Missing required fields: {', '.join(missing)}"}
            )
