from django.urls import path

from apps.ui.views import DashboardLayoutStateView, NavigationStateView

urlpatterns = [
    path("ui/dashboard-layouts/", DashboardLayoutStateView.as_view(), name="ui-dashboard-layout-state"),
    path("ui/navigation-state/", NavigationStateView.as_view(), name="ui-navigation-state"),
]
