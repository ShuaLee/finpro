"""
subscriptions.urls
~~~~~~~~~~~~~~~~~~~
Defines URL routes for subscription-related API endpoints.
"""

from django.urls import path
from subscriptions.views import PlanListView, AccountTypeListView

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='plan-list'),
    path('account-types/', AccountTypeListView.as_view(), name='account-type-list'),
]
