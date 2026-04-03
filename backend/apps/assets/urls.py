from django.urls import path

from apps.assets.views import (
    AssetDetailView,
    AssetListCreateView,
    AssetTypeDetailView,
    AssetTypeListCreateView,
)

urlpatterns = [
    path("asset-types/", AssetTypeListCreateView.as_view(), name="asset-type-list-create"),
    path("asset-types/<int:pk>/", AssetTypeDetailView.as_view(), name="asset-type-detail"),
    path("assets/", AssetListCreateView.as_view(), name="asset-list-create"),
    path("assets/<uuid:pk>/", AssetDetailView.as_view(), name="asset-detail"),
]
