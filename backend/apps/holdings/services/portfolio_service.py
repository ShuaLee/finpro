from django.core.exceptions import ValidationError

from apps.holdings.models import Portfolio


class PortfolioService:
    @staticmethod
    def ensure_default_portfolio(*, profile) -> Portfolio:
        portfolio, _ = Portfolio.objects.get_or_create(
            profile=profile,
            is_default=True,
            defaults={
                "name": "Main Portfolio",
                "kind": Portfolio.Kind.PERSONAL,
            },
        )
        return portfolio

    @staticmethod
    def create_portfolio(
        *,
        profile,
        name: str,
        kind: str = Portfolio.Kind.PERSONAL,
        is_default: bool = False,
    ) -> Portfolio:
        portfolio = Portfolio(
            profile=profile,
            name=(name or "").strip(),
            kind=kind,
            is_default=is_default,
        )
        portfolio.save()
        return portfolio

    @staticmethod
    def update_portfolio(
        *,
        portfolio: Portfolio,
        profile,
        name: str | None = None,
        kind: str | None = None,
        is_default: bool | None = None,
    ) -> Portfolio:
        if portfolio.profile != profile:
            raise ValidationError("You cannot edit another user's portfolio.")

        if name is not None:
            portfolio.name = name
        if kind is not None:
            portfolio.kind = kind
        if is_default is not None:
            portfolio.is_default = is_default

        portfolio.save()
        return portfolio
