from django.core.exceptions import ValidationError
from users.models import Profile
from subscriptions.models import Plan, AccountType
from portfolios.services.portfolio_manager import PortfolioManager
from fx.models.country import Country
from fx.models.fx import FXCurrency


class ProfileService:
    """
    Service class for handling lifecycle and business logic of Profiles.
    """

    # ------------------------------
    # Bootstrap
    # ------------------------------
    @staticmethod
    def bootstrap(user) -> Profile:
        """
        Initialize a Profile for a new user with sane defaults:
          - Default Free plan
          - Default AccountType: Individual Investor
          - Ensures Main Portfolio exists for this profile
        """
        profile, _ = Profile.objects.get_or_create(user=user)

        # Assign Free plan if none exists
        if not profile.plan:
            free_plan = Plan.objects.filter(slug="free").first()
            if not free_plan:
                raise ValidationError(
                    {"detail": "Default Free plan not found. Please initialize plans."}
                )
            profile.plan = free_plan

        # Assign Individual Investor account type if none exists
        if not profile.account_type:
            individual_type = AccountType.objects.filter(
                slug="individual").first()
            if not individual_type:
                raise ValidationError(
                    {"detail": "Default AccountType 'individual' not found."}
                )
            profile.account_type = individual_type

        # Assign Default Currency (USD) if missing
        if not profile.currency:
            usd = FXCurrency.objects.filter(code="USD").first()
            if not usd:
                raise ValidationError(
                    {"detail": "FXCurrency 'USD' not found. Run: python manage.py sync_fx_universe"}
                )
            profile.currency = usd

        if not profile.country:
            us = Country.objects.filter(code="US").first()
            if not us:
                raise ValidationError(
                    {"detail": "Country 'US' not found. Run sync."}
                )

        # Ensure Portfolio exists for this Profile
        PortfolioManager.ensure_main_portfolio(profile)

        profile.save(update_fields=["plan", "account_type", "currency"])
        return profile

    # ------------------------------
    # Validation
    # ------------------------------
    @staticmethod
    def validate_required_fields(data: dict, partial: bool = False):
        """
        Ensures that required profile fields are provided when updating profile.

        Args:
            data (dict): Incoming validated data from serializer.
            partial (bool): Whether this is a partial update (PATCH).

        Raises:
            ValidationError: If required fields are missing.
        """
        # -----------------------------------------
    # REQUIRED FIELDS CHECK (currency only)
    # -----------------------------------------
        if not partial:
            missing = []

            # Currency is required for full updates
            if not data.get("currency"):
                missing.append("currency")

            if missing:
                raise ValidationError(
                    {"detail": f"Missing required fields: {', '.join(missing)}"}
                )

        # -----------------------------------------
        # COUNTRY VALIDATION (optional but strict)
        # -----------------------------------------
        if "country" in data:
            country_val = data.get("country")

            # Allow null explicitly (user removing country)
            if country_val is None:
                return

            # Validate FK exists
            if not Country.objects.filter(pk=country_val).exists():
                raise ValidationError(
                    {"country": "Invalid or unknown country code."}
                )