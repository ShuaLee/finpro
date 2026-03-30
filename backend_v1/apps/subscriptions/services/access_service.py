from django.core.exceptions import ObjectDoesNotExist, ValidationError


class SubscriptionAccessService:
    @staticmethod
    def get_effective_plan(profile):
        try:
            subscription = profile.subscription
        except ObjectDoesNotExist:
            subscription = None
        if subscription and subscription.plan and subscription.status in {"active", "trialing"}:
            return subscription.plan
        return profile.plan

    @staticmethod
    def can_create_client_portfolio(profile) -> bool:
        plan = SubscriptionAccessService.get_effective_plan(profile)
        return bool(plan and plan.client_mode_enabled)

    @staticmethod
    def get_max_portfolios(profile):
        plan = SubscriptionAccessService.get_effective_plan(profile)
        return plan.max_portfolios if plan else 1

    @staticmethod
    def assert_can_create_portfolio(*, profile, kind: str, existing_count: int):
        max_portfolios = SubscriptionAccessService.get_max_portfolios(profile)
        if max_portfolios is not None and existing_count >= max_portfolios:
            raise ValidationError("Portfolio limit reached for current subscription plan.")

        if kind == "client" and not SubscriptionAccessService.can_create_client_portfolio(profile):
            raise ValidationError("Client portfolios are available on the Wealth Manager tier.")
