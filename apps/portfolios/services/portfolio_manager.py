from django.core.exceptions import ValidationError
from django.db import transaction
from users.models import Profile
from portfolios.models.portfolio import Portfolio


class PortfolioManager:
    """
    Service class to handle lifecycle operations for user portfolios.
    """

    # -------------------------------
    # Main Portfolio Methods
    # -------------------------------
    @staticmethod
    def create_main_portfolio(profile: Profile, name: str = "Main Portfolio") -> Portfolio:
        """
        Creates the main Portfolio for the given profile.
        Raises ValidationError if one already exists.
        """
        if Portfolio.objects.filter(profile=profile, is_main=True).exists():
            raise ValidationError(
                f"Profile {profile.id} already has a main portfolio.")
        with transaction.atomic():
            return Portfolio.objects.create(
                profile=profile,
                name=name,
                is_main=True,
            )

    @staticmethod
    def ensure_main_portfolio(profile: Profile) -> Portfolio:
        """
        Ensures the profile has a main portfolio (idempotent).
        Returns existing or newly created main portfolio.
        """
        portfolio, _ = Portfolio.objects.get_or_create(
            profile=profile,
            is_main=True,
            defaults={"name": "Main Portfolio"}
        )
        return portfolio

    @staticmethod
    def get_main_portfolio(profile: Profile) -> Portfolio:
        """
        Fetch the main Portfolio for a profile.
        Raises ValidationError if not found.
        """
        try:
            return Portfolio.objects.get(profile=profile, is_main=True)
        except Portfolio.DoesNotExist:
            raise ValidationError(
                f"No main portfolio exists for profile {profile.id}")
