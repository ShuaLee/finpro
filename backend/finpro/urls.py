from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth + identity
    path("api/v1/auth/", include("users.urls.auth_urls")),
    path("api/v1/user/", include("profiles.urls.profile_urls")),

    # Plan metadata
    path("api/v1/subscriptions/", include("subscriptions.urls")),
    path("api/v1/accounts/", include("accounts.urls")),
    path("api/v1/portfolios/", include("portfolios.urls")),
    path("api/v1/assets/", include("assets.urls")),
    path("api/v1/analytics/", include("analytics.urls")),
    path("api/v1/allocations/", include("allocations.urls")),
]
