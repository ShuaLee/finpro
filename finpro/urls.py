from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.users.auth_urls')), # all auth endpoints
    path('api/v1/users/', include('apps.users.profile_urls')), # profile endpoint(s)
    path('api/v1/portfolios/', include('apps.portfolios.urls')), # future app
]
