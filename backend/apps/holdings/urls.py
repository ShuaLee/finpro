from django.urls import path

from apps.holdings.views import (
    ContainerDetailView,
    ContainerListCreateView,
    HoldingFactDefinitionDetailView,
    HoldingFactDefinitionListCreateView,
    HoldingFactValueListUpsertView,
    HoldingOverrideDetailView,
    HoldingOverrideListUpsertView,
    HoldingCreateWithAssetView,
    HoldingDetailView,
    HoldingListCreateView,
    DashboardLayoutStateView,
    PortfolioDetailView,
    PortfolioListCreateView,
)

urlpatterns = [
    path("portfolios/dashboard-layouts/", DashboardLayoutStateView.as_view(), name="dashboard-layout-state"),
    path("portfolios/", PortfolioListCreateView.as_view(), name="portfolio-list-create"),
    path("portfolios/<int:pk>/", PortfolioDetailView.as_view(), name="portfolio-detail"),
    path("containers/", ContainerListCreateView.as_view(), name="container-list-create"),
    path("containers/<int:pk>/", ContainerDetailView.as_view(), name="container-detail"),
    path("holdings/", HoldingListCreateView.as_view(), name="holding-list-create"),
    path("holdings/create-with-asset/", HoldingCreateWithAssetView.as_view(), name="holding-create-with-asset"),
    path("holdings/<int:pk>/", HoldingDetailView.as_view(), name="holding-detail"),
    path("holdings/<int:pk>/facts/", HoldingFactValueListUpsertView.as_view(), name="holding-fact-list-upsert"),
    path("holdings/<int:pk>/overrides/", HoldingOverrideListUpsertView.as_view(), name="holding-override-list-upsert"),
    path("holding-overrides/<int:override_id>/", HoldingOverrideDetailView.as_view(), name="holding-override-detail"),
    path("holding-fact-definitions/", HoldingFactDefinitionListCreateView.as_view(), name="holding-fact-definition-list-create"),
    path("holding-fact-definitions/<int:pk>/", HoldingFactDefinitionDetailView.as_view(), name="holding-fact-definition-detail"),
]
