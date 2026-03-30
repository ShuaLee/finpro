from django.urls import path

from analytics.views import (
    AnalyticDetailView,
    AnalyticLatestResultsView,
    AnalyticListCreateView,
    AnalyticRunView,
    AssetExposureDetailView,
    AssetExposureListUpsertView,
    BucketDetailView,
    BucketListCreateView,
    DimensionDetailView,
    DimensionListCreateView,
    HoldingOverrideDetailView,
    HoldingOverrideListUpsertView,
)

urlpatterns = [
    path("", AnalyticListCreateView.as_view(), name="analytics-list-create"),
    path("<int:analytic_id>/", AnalyticDetailView.as_view(), name="analytics-detail"),
    path("<int:analytic_id>/run/", AnalyticRunView.as_view(), name="analytics-run"),
    path("<int:analytic_id>/results/latest/", AnalyticLatestResultsView.as_view(), name="analytics-results-latest"),
    path("<int:analytic_id>/dimensions/", DimensionListCreateView.as_view(), name="analytics-dimension-list-create"),
    path("dimensions/<int:dimension_id>/", DimensionDetailView.as_view(), name="analytics-dimension-detail"),
    path("dimensions/<int:dimension_id>/buckets/", BucketListCreateView.as_view(), name="analytics-bucket-list-create"),
    path("buckets/<int:bucket_id>/", BucketDetailView.as_view(), name="analytics-bucket-detail"),
    path(
        "dimensions/<int:dimension_id>/asset-exposures/",
        AssetExposureListUpsertView.as_view(),
        name="analytics-asset-exposure-list-upsert",
    ),
    path("asset-exposures/<int:exposure_id>/", AssetExposureDetailView.as_view(), name="analytics-asset-exposure-detail"),
    path(
        "dimensions/<int:dimension_id>/holding-overrides/",
        HoldingOverrideListUpsertView.as_view(),
        name="analytics-holding-override-list-upsert",
    ),
    path("holding-overrides/<int:override_id>/", HoldingOverrideDetailView.as_view(), name="analytics-holding-override-detail"),
]
