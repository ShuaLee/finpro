from rest_framework import serializers

from subscriptions.models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_slug = serializers.CharField(source="plan.slug", read_only=True)
    plan_tier = serializers.CharField(source="plan.tier", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "status",
            "plan",
            "plan_slug",
            "plan_tier",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "ended_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "plan_slug",
            "plan_tier",
            "created_at",
            "updated_at",
        ]

