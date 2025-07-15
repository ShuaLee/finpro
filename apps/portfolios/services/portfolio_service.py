"""
Portfolio Service
-----------------

This module provides services for creating and managing main Portfolio objects.
All business logic related to the `Portfolio` model is centralized here.

Responsibilities:
- Create new portfolio linked to a user profile.
- Retrieve existing portfolio.
- Mark portfolio setup as complete.
"""

from django.db import transaction
from users.models import Profile
from portfolios.models import Portfolio


def create_portfolio(profile: Profile) -> Portfolio:
    """
    Creates a new Portfolio for the given user profile.

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
        ObjectDoesNotExist: If the portfolio does not exist.
    """
    return Portfolio.objects.get(profile=profile)

