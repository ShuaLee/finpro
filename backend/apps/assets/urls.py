from django.urls import path

from assets.views import (
    AssetTypeListView,
    AssetsHealthView,
    CustomAssetDetailView,
    CustomAssetListCreateView,
    CustomAssetTypeCreateView,
    CustomAssetTypeDetailView,
    RealEstateAssetDetailView,
    RealEstateAssetListCreateView,
    RealEstateTypeCreateView,
    RealEstateTypeDetailView,
    RealEstateTypeListView,
)

urlpatterns = [
    path("health/", AssetsHealthView.as_view(), name="assets-health"),
    path("asset-types/", AssetTypeListView.as_view(), name="asset-type-list"),
    path("asset-types/custom/", CustomAssetTypeCreateView.as_view(), name="asset-type-custom-create"),
    path("asset-types/custom/<int:type_id>/", CustomAssetTypeDetailView.as_view(), name="asset-type-custom-detail"),
    path("custom-assets/", CustomAssetListCreateView.as_view(), name="custom-asset-list-create"),
    path("custom-assets/<uuid:asset_id>/", CustomAssetDetailView.as_view(), name="custom-asset-detail"),
    path("real-estate-types/", RealEstateTypeListView.as_view(), name="real-estate-type-list"),
    path("real-estate-types/custom/", RealEstateTypeCreateView.as_view(), name="real-estate-type-custom-create"),
    path("real-estate-types/custom/<int:type_id>/", RealEstateTypeDetailView.as_view(), name="real-estate-type-custom-detail"),
    path("real-estate-assets/", RealEstateAssetListCreateView.as_view(), name="real-estate-asset-list-create"),
    path("real-estate-assets/<uuid:asset_id>/", RealEstateAssetDetailView.as_view(), name="real-estate-asset-detail"),
]
