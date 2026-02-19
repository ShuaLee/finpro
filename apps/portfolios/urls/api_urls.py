from django.urls import path

from portfolios.views import (
    PortfolioDenominationDetailView,
    PortfolioDenominationListCreateView,
    PortfolioValuationSnapshotCaptureView,
    PortfolioValuationSnapshotListView,
    PortfolioValuationView,
)

urlpatterns = [
    path("<int:portfolio_id>/valuation/", PortfolioValuationView.as_view(), name="portfolio-valuation"),
    path(
        "<int:portfolio_id>/valuation/snapshots/capture/",
        PortfolioValuationSnapshotCaptureView.as_view(),
        name="portfolio-valuation-snapshot-capture",
    ),
    path(
        "<int:portfolio_id>/valuation/snapshots/",
        PortfolioValuationSnapshotListView.as_view(),
        name="portfolio-valuation-snapshot-list",
    ),
    path(
        "<int:portfolio_id>/denominations/",
        PortfolioDenominationListCreateView.as_view(),
        name="portfolio-denomination-list-create",
    ),
    path(
        "denominations/<int:denomination_id>/",
        PortfolioDenominationDetailView.as_view(),
        name="portfolio-denomination-detail",
    ),
]
