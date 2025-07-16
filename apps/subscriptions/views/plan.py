"""
subscriptions.views
~~~~~~~~~~~~~~~~~~~~
Defines API endpoints for subscription-related actions,
such as listing available plans.
"""

from rest_framework import generics
from subscriptions.models import Plan
from subscriptions.serializers import PlanSerializer


class PlanListView(generics.ListAPIView):
    """
    API endpoint to list all active subscription plans.

    This endpoint is used to display available subscription options to users.
    Useful for:
        - Sign-up flows (show available plans)
        - Profile upgrade screens
        - Billing pages

    Method:
        GET /subscriptions/plans/

    Response Example:
        [
            {
                "name": "Free",
                "slug": "free",
                "description": "Basic plan with limited features",
                "max_stocks": 10,
                "allow_crypto": false,
                "allow_metals": false,
                "price_per_month": "0.00"
            },
            {
                "name": "Premium",
                "slug": "premium",
                "description": "Unlimited access with crypto and metals",
                "max_stocks": 9999,
                "allow_crypto": true,
                "allow_metals": true,
                "price_per_month": "9.99"
            }
        ]
    """

    serializer_class = PlanSerializer

    def get_queryset(self):
        """
        Return all active plans sorted by price.
        """
        return Plan.objects.filter(is_active=True).order_by('price_per_month')
