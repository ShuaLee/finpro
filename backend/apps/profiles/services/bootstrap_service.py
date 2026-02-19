from django.core.exceptions import ValidationError
from django.db import transaction

from fx.models.country import Country
from fx.models.fx import FXCurrency
from profiles.models import Profile
from subscriptions.models import Plan
from subscriptions.services import SubscriptionService


class ProfileBootstrapService:
    @staticmethod
    @transaction.atomic
    def bootstrap(*, user):
        usd = FXCurrency.objects.filter(code="USD", is_active=True).first()
        if not usd:
            raise ValidationError("Default currency USD not found.")

        free_plan = Plan.objects.filter(slug="free", is_active=True).first()
        if not free_plan:
            raise ValidationError("Default plan 'free' not found.")

        us = Country.objects.filter(code="US", is_active=True).first()

        # currency is required; include it in defaults so initial create is valid
        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={
                "currency": usd,
                "country": us,
                "plan": free_plan,
                "language": "en",
                "timezone": "UTC",
            },
        )

        updated_fields = []

        if not profile.currency:
            profile.currency = usd
            updated_fields.append("currency")

        if not profile.country and us:
            profile.country = us
            updated_fields.append("country")

        if not profile.plan:
            profile.plan = free_plan
            updated_fields.append("plan")

        if not profile.language:
            profile.language = "en"
            updated_fields.append("language")

        if not profile.timezone:
            profile.timezone = "UTC"
            updated_fields.append("timezone")

        if updated_fields:
            profile.save(update_fields=updated_fields + ["updated_at"])

        SubscriptionService.ensure_default_subscription(
            profile=profile,
            default_plan=free_plan,
        )

        # Ensure personal portfolio exists
        try:
            from portfolios.services.portfolio_manager import PortfolioManager
        except Exception as exc:
            raise ValidationError(
                "Portfolio service unavailable. Ensure 'portfolios' app is installed."
            ) from exc

        PortfolioManager.ensure_personal_portfolio(profile)

        return profile
