from users.models import Profile
from portfolios.models import Portfolio

def bootstrap_user_profile_and_portfolio(user):
    """
    Create a Profile and Portfolio for a newly created user.
    Idempotent: will not duplicate objects if they already exist.
    """

    profile, _ = Profile.objects.get_or_create(user=user)
    Portfolio.objects.get_or_create(profile=profile)
    return profile