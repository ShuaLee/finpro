from django.urls import include, path

urlpatterns = [
    path("stocks/", include("accounts.urls.stocks")),
    # Future: path("metals/", include("accounts.urls.metals")),
    # Future: path("crypto/", include("accounts.urls.crypto")),
]