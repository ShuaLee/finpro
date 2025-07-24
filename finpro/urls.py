from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # all auth endpoints
    path('api/v1/auth/', include('apps.users.urls.auth_urls')),
    # profile endpoint(s)
    path('api/v1/users/', include('apps.users.urls.profile_urls')),
    path('api/v1/', include('common.urls')),
    path('api/v1/portfolios/', include('apps.portfolios.urls')),
    # -> off for tests -> path('api/v1/accounts/stocks/', include('accounts.urls.stocks')),
    # -> off for tests ->  path('api/v1/accounts/metals/', include('accounts.urls.metals_urls')),
]
