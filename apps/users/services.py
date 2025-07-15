"""
users.services
~~~~~~~~~~~~~~
Contains service functions that encapsulate domain logic related to users.
These functions help keep views thin by handling business processes separately.
"""


from users.models import Profile
from portfolios.models import Portfolio


def bootstrap_user_profile_and_portfolio(user):
    """
    Initializes essential related objects for a new user.

    This function ensures that when a user signs up:
    - A Profile is linked to the User.
    - A default Portfolio is created for that Profile.

    Args:
        user (User): The newly created User instance.

    Returns:
        Profile: The created or existing Profile instance.
    """

    profile, _ = Profile.objects.get_or_create(user=user)
    Portfolio.objects.get_or_create(profile=profile)
    return profile
