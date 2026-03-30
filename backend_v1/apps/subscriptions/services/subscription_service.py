from django.db import transaction
from django.utils import timezone

from django.core.exceptions import ValidationError

from subscriptions.models import Plan, Subscription


class SubscriptionService:
    @staticmethod
    @transaction.atomic
    def ensure_default_subscription(*, profile, default_plan):
        subscription, created = Subscription.objects.get_or_create(
            profile=profile,
            defaults={
                "plan": default_plan,
                "status": Subscription.Status.ACTIVE,
                "current_period_start": timezone.now(),
            },
        )

        if not created and subscription.plan_id is None:
            subscription.plan = default_plan
            subscription.save(update_fields=["plan", "updated_at"])

        if profile.plan_id != subscription.plan_id:
            profile.plan = subscription.plan
            profile.save(update_fields=["plan", "updated_at"])

        return subscription

    @staticmethod
    @transaction.atomic
    def change_plan(*, profile, plan: Plan, status: str = Subscription.Status.ACTIVE):
        if plan is None:
            raise ValidationError("Target plan is required.")

        subscription, _ = Subscription.objects.get_or_create(
            profile=profile,
            defaults={
                "plan": plan,
                "status": status,
                "current_period_start": timezone.now(),
            },
        )

        changed_fields = []
        if subscription.plan_id != plan.id:
            subscription.plan = plan
            changed_fields.append("plan")

        if subscription.status != status:
            subscription.status = status
            changed_fields.append("status")

        if not subscription.current_period_start:
            subscription.current_period_start = timezone.now()
            changed_fields.append("current_period_start")

        if changed_fields:
            subscription.save(update_fields=changed_fields + ["updated_at"])

        if profile.plan_id != plan.id:
            profile.plan = plan
            profile.save(update_fields=["plan", "updated_at"])

        return subscription

    @staticmethod
    @transaction.atomic
    def downgrade_to_free(*, profile):
        free_plan = Plan.objects.filter(slug="free", is_active=True).first()
        if not free_plan:
            raise ValidationError("Default plan 'free' not found.")
        return SubscriptionService.change_plan(profile=profile, plan=free_plan)
