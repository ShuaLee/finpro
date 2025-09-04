from django.core.exceptions import ValidationError
from django.db import transaction
from users.models import Profile
from portfolios.models.portfolio import Portfolio


class PortfolioManager:
    """
    Service class to handle lifecycle operations for user portfolios
    and their sub-portfolios.
    """

    # -------------------------------
    # Main Portfolio Methods
    # -------------------------------
    @staticmethod
    def create_portfolio(profile: Profile) -> Portfolio:
        """
        Creates a new Portfolio for the given profile.
        Raises ValidationError if one already exists.
        """
        if hasattr(profile, "portfolio"):
            raise ValueError(f"Profile {profile.id} already has a portfolio.")
        
        with transaction.atomic():
            return Portfolio.objects.create(profile=profile)
        
    @staticmethod    
    def ensure_portfolio_for_profile(profile: Profile) -> Portfolio:
        """
        Ensures the profile has a portfolio (idempotent).
        Returns existing or newly created portfolio.
        """
        portfolio, _ = Portfolio.objects.get_or_create(profile=profile)
        return portfolio
    
    @staticmethod
    def get_portfolio(profile: Profile) -> Portfolio:
        """
        Fetch the main Portfolio for a profile.
        Raises ValidationError if not found.
        """
        if not hasattr(profile, "portfolio"):
            raise ValidationError("No portfolio exists for this profile.")
        return profile.portfolio
    
