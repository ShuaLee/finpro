from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from portfolios.services import PortfolioManager
from profiles.models import Profile
from subscriptions.models import Plan
from subscriptions.services import SubscriptionService


@receiver(post_save, sender=Profile)
def ensure_profile_foundations(sender, instance, created, **kwargs):
    if not created:
        return

    def _ensure():
        default_plan = instance.plan or Plan.objects.filter(slug="free", is_active=True).first()
        if default_plan:
            SubscriptionService.ensure_default_subscription(
                profile=instance,
                default_plan=default_plan,
            )
        PortfolioManager.ensure_main_portfolio(instance)

    transaction.on_commit(_ensure)

