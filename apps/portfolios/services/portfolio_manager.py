from django.core.exceptions import ValidationError
from django.db import transaction

from profiles.models import Profile
from portfolios.models.portfolio import Portfolio
from subscriptions.services import SubscriptionAccessService


class PortfolioManager:
    """
    Service class to handle lifecycle operations for user portfolios.
    """

    @staticmethod
    def ensure_personal_portfolio(profile: Profile) -> Portfolio:
        """
        Ensures the profile has a personal portfolio (idempotent).
        Returns existing or newly created personal portfolio.
        """
        portfolio, _ = Portfolio.objects.get_or_create(
            profile=profile,
            kind=Portfolio.Kind.PERSONAL,
            defaults={
                "name": "Main Portfolio",
                "client_name": None,
            },
        )
        updated_fields = []
        if portfolio.kind != Portfolio.Kind.PERSONAL:
            portfolio.kind = Portfolio.Kind.PERSONAL
            updated_fields.append("kind")
        if portfolio.client_name:
            portfolio.client_name = None
            updated_fields.append("client_name")
        if updated_fields:
            portfolio.save(update_fields=updated_fields)
        return portfolio

    @staticmethod
    def get_personal_portfolio(profile: Profile) -> Portfolio:
        """
        Fetch the personal portfolio for a profile.
        Raises ValidationError if not found.
        """
        try:
            return Portfolio.objects.get(profile=profile, kind=Portfolio.Kind.PERSONAL)
        except Portfolio.DoesNotExist:
            raise ValidationError(f"No personal portfolio exists for profile {profile.id}")

    @staticmethod
    @transaction.atomic
    def create_portfolio(
        *,
        profile: Profile,
        name: str,
        kind: str = Portfolio.Kind.PERSONAL,
        client_name: str | None = None,
    ) -> Portfolio:
        if kind not in Portfolio.Kind.values:
            raise ValidationError("Invalid portfolio kind.")

        normalized_name = (name or "").strip()
        if not normalized_name:
            raise ValidationError("Portfolio name is required.")

        if kind == Portfolio.Kind.CLIENT and not (client_name or "").strip():
            raise ValidationError("Client name is required for client portfolios.")
        if kind == Portfolio.Kind.PERSONAL:
            raise ValidationError("Only one personal portfolio is allowed per profile.")

        existing_count = Portfolio.objects.filter(profile=profile).count()
        SubscriptionAccessService.assert_can_create_portfolio(
            profile=profile,
            kind=kind,
            existing_count=existing_count,
        )

        return Portfolio.objects.create(
            profile=profile,
            name=normalized_name,
            kind=kind,
            client_name=(client_name or "").strip() or None,
        )
