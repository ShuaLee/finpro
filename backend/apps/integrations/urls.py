from django.urls import path

from apps.integrations.views import ActiveEquityListView

urlpatterns = [
    path("active-equities/", ActiveEquityListView.as_view(), name="active-equity-list"),
]
