"""
users.services
~~~~~~~~~~~~~~
Contains service functions that encapsulate domain logic related to users.
These functions help keep views thin by handling business processes separately.
"""


from users.models import Profile
from portfolios.models import Portfolio


def bootstrap_user_profile_and_portfolio(user, country="US", preferred_currency="USD"):
    """
    Initializes essential related objects for a new user.

    Creates a Profile and a default Portfolio with optional preferences.

    Args:
        user (User): The newly created user.
        country (str): Country code (ISO alpha-2).
        preferred_currency (str): Currency code (ISO alpha-3).

    Returns:
        Profile: The created or existing Profile instance.
    """
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.country = country
    profile.preferred_currency = preferred_currency
    profile.save(update_fields=["country", "preferred_currency"])

    Portfolio.objects.get_or_create(profile=profile)
    return profile