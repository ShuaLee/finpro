"""
users.services
~~~~~~~~~~~~~~
Contains service functions that encapsulate domain logic related to users.
These functions help keep views thin by handling business processes separately.
"""

from rest_framework.exceptions import ValidationError
from users.models import Profile
from portfolios.models.portfolio import Portfolio
from subscriptions.models import Plan


def bootstrap_user_profile_and_portfolio(user, country="US", preferred_currency="USD"):
    """
    Initializes essential related objects for a new user.

    Creates:
        - A Profile linked to the user, with default country, currency, and Free plan.
        - A default Portfolio linked to that Profile.

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

    # Assign defaults
    profile.country = country
    profile.preferred_currency = preferred_currency

    # ✅ Assign Free plan if none exists
    if not profile.plan:
        free_plan = Plan.objects.filter(slug="free").first()
        if not free_plan:
            raise ValidationError(
                {"detail": "Default Free plan not found. Please initialize plans."})
        profile.plan = free_plan

    profile.save(update_fields=["country", "preferred_currency", "plan"])

    # Create a portfolio for this profile if not present
    Portfolio.objects.get_or_create(profile=profile)
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
