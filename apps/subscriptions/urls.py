"""
subscriptions.urls
~~~~~~~~~~~~~~~~~~~
Defines URL routes for subscription-related API endpoints.
"""

from django.urls import path
from subscriptions.views import PlanListView

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='plan-list'),
]
