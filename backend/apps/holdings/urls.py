from django.urls import path

from apps.holdings.views import (
    ContainerDetailView,
    ContainerListCreateView,
    HoldingCreateWithAssetView,
    HoldingDetailView,
    HoldingListCreateView,
    PortfolioDetailView,
    PortfolioListCreateView,
)

urlpatterns = [
    path("portfolios/", PortfolioListCreateView.as_view(), name="portfolio-list-create"),
    path("portfolios/<int:pk>/", PortfolioDetailView.as_view(), name="portfolio-detail"),
    path("containers/", ContainerListCreateView.as_view(), name="container-list-create"),
    path("containers/<int:pk>/", ContainerDetailView.as_view(), name="container-detail"),
    path("holdings/", HoldingListCreateView.as_view(), name="holding-list-create"),
    path("holdings/create-with-asset/", HoldingCreateWithAssetView.as_view(), name="holding-create-with-asset"),
    path("holdings/<int:pk>/", HoldingDetailView.as_view(), name="holding-detail"),
]
