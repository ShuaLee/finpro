from django.core.exceptions import ValidationError
from django.db import transaction

from profiles.models import Profile
from portfolios.models.portfolio import Portfolio
from subscriptions.services import SubscriptionAccessService


class PortfolioManager:
    """
    Service class to handle lifecycle operations for user portfolios.
    """

    # -------------------------------
    # Main Portfolio Methods
    # -------------------------------
    # @staticmethod
    # def create_main_portfolio(profile: Profile, name: str = "Main Portfolio") -> Portfolio:
    #     """
    #     Creates the main Portfolio for the given profile.
    #     Raises ValidationError if one already exists.
    #     """
    #     if Portfolio.objects.filter(profile=profile, is_main=True).exists():
    #         raise ValidationError(
    #             f"Profile {profile.id} already has a main portfolio.")
    #     with transaction.atomic():
    #         return Portfolio.objects.create(
    #             profile=profile,
    #             name=name,
    #             is_main=True,
    #         )

    @staticmethod
    def ensure_main_portfolio(profile: Profile) -> Portfolio:
        """
        Ensures the profile has a main portfolio (idempotent).
        Returns existing or newly created main portfolio.
        """
        portfolio, _ = Portfolio.objects.get_or_create(
            profile=profile,
            is_main=True,
            defaults={
                "name": "Main Portfolio",
                "kind": Portfolio.Kind.PERSONAL,
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
            is_main=False,
        )
