"""
Portfolio Service
-----------------

Centralizes Portfolio-related business logic:
- Safe creation for user bootstrap (idempotent).
- Dedicated creation for manual setups (strict).
- Retrieval helpers.
"""

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from users.models import Profile
from portfolios.models.portfolio import Portfolio


def create_portfolio(profile: Profile) -> Portfolio:
    """
    Creates a new Portfolio for the given profile.
    Strict: Raises an error if a portfolio already exists.

    Args:
        profile (Profile): The user's profile instance.

    Returns:
        Portfolio: The newly created Portfolio instance.

    Raises:
        ValueError: If the profile already has a portfolio.
    """
    if hasattr(profile, "portfolio"):
        raise ValueError(f"Profile {profile.id} already has a portfolio.")

    with transaction.atomic():
        portfolio = Portfolio.objects.create(profile=profile)
        return portfolio


def get_portfolio(profile: Profile) -> Portfolio:
    """
    Retrieves the Portfolio associated with the given profile.

    Args:
        profile (Profile): The user's profile.

    Returns:
        Portfolio: The portfolio linked to the profile.

    Raises:
        ObjectDoesNotExist: If no portfolio exists.
    """
    return Portfolio.objects.get(profile=profile)


def ensure_portfolio_for_profile(profile: Profile) -> Portfolio:
    """
    Ensures the profile has a portfolio (idempotent).
    Used during user bootstrap or system defaults.

    Args:
        profile (Profile): The user's profile.

    Returns:
        Portfolio: Existing or newly created portfolio.
    """
    portfolio, _ = Portfolio.objects.get_or_create(profile=profile)
    return portfolio