from django.urls import path

from assets.views import AssetsHealthView

urlpatterns = [
    path("health/", AssetsHealthView.as_view(), name="assets-health"),
]
