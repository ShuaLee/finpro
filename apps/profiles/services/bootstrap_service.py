from django.core.exceptions import ValidationError
from django.db import transaction

from fx.models.country import Country
from fx.models.fx import FXCurrency
from profiles.models import Profile
from subscriptions.models import AccountType, Plan


class ProfileBootstrapService:
    @staticmethod
    @transaction.atomic
    def bootstrap(*, user):
        profile, _ = Profile.objects.get_or_create(user=user)

        updated_fields = []

        if not profile.currency:
            usd = FXCurrency.objects.filter(code="USD").first()
            if not usd:
                raise ValidationError("Default currency USD not found.")
            profile.currency = usd
            updated_fields.append("currency")

        if not profile.country:
            us = Country.objects.filter(code="US").first()
            if us:
                profile.country = us
                updated_fields.append("country")

        if not profile.plan:
            free_plan = Plan.objects.filter(slug="free", is_active=True).first()
            if not free_plan:
                raise ValidationError("Default plan 'free' not found.")
            profile.plan = free_plan
            updated_fields.append("plan")

        if not profile.account_type:
            default_account_type = AccountType.objects.filter(slug="individual").first()
            if not default_account_type:
                raise ValidationError("Default account type 'individual' not found.")
            profile.account_type = default_account_type
            updated_fields.append("account_type")

        if not profile.language:
            profile.language = "en"
            updated_fields.append("language")

        if not profile.timezone:
            profile.timezone = "UTC"
            updated_fields.append("timezone")

        if updated_fields:
            profile.save(update_fields=updated_fields + ["updated_at"])

        # Ensure main portfolio exists
        try:
            from portfolios.services.portfolio_manager import PortfolioManager
        except Exception as exc:
            raise ValidationError(
                "Portfolio service unavailable. Ensure 'portfolios' app is installed."
            ) from exc

        PortfolioManager.ensure_main_portfolio(profile)

        return profile
