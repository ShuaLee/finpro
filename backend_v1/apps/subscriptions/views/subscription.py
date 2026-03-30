from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.serializers import SubscriptionSerializer
from subscriptions.services import SubscriptionService


class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        try:
            subscription = profile.subscription
        except ObjectDoesNotExist:
            subscription = None

        if subscription is None:
            if profile.plan is None:
                return Response({"detail": "No subscription or fallback plan available."}, status=404)
            subscription = SubscriptionService.ensure_default_subscription(
                profile=profile,
                default_plan=profile.plan,
            )

        return Response(SubscriptionSerializer(subscription).data, status=200)
