"""
Portfolio Service
-----------------
Handles creation and retrieval logic for user portfolios.
"""

from django.db import transaction
from users.models import Profile
from portfolios.models.portfolio import Portfolio


def create_portfolio(profile: Profile) -> Portfolio:
    """
    Creates a new Portfolio for the given profile.
    Raises an error if the profile already has one.
    """
    if hasattr(profile, "portfolio"):
        raise ValueError(f"Profile {profile.id} already has a portfolio.")

    with transaction.atomic():
        return Portfolio.objects.create(profile=profile)


def ensure_portfolio_for_profile(profile: Profile) -> Portfolio:
    """
    Ensures the profile has a portfolio (idempotent).
    Returns existing or newly created portfolio.
    """
    portfolio, _ = Portfolio.objects.get_or_create(profile=profile)
    return portfolio
