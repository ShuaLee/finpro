"""
users.services
~~~~~~~~~~~~~~
Contains service functions that encapsulate domain logic related to users.
These functions help keep views thin by handling business processes separately.
"""

from rest_framework.exceptions import ValidationError
from users.models import Profile
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
    from apps.portfolios.services.portfolio_management import ensure_portfolio_for_profile

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
            raise ValidationError(
                {"detail": "Default AccountType 'individual' not found."})
        profile.account_type = individual_type

    # Ensure Portfolio exists for this Profile
    ensure_portfolio_for_profile(profile)

    # ✅ Set completion status
    profile.is_profile_complete = check_profile_completion(profile)
    profile.save(update_fields=["plan", "account_type", "is_profile_complete"])

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
        if not data.get('currency'):
            missing.append('currency')
        if missing:
            raise ValidationError(
                {"detail": f"Missing required fields: {', '.join(missing)}"}
            )


def check_profile_completion(profile):
    """
    Determine if a user's profile has all required fields filled in.

    Required fields:
        - full_name
        - country
        - currency

    Args:
        profile (Profile): The profile instance to check.

    Returns:
        bool: True if profile is complete, False otherwise.
    """
    required_fields = ['full_name', 'country', 'currency']
    return all(getattr(profile, field) for field in required_fields)


def update_profile_completion(profile):
    """
    Update the is_profile_complete flag based on current profile data.

    Args:
        profile (Profile): The user's profile.
    """
    profile.is_profile_complete = check_profile_completion(profile)
    profile.save(update_fields=['is_profile_complete'])
