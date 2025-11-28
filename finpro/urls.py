from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # # all auth endpoints
    # path('api/v1/auth/', include('apps.users.urls.auth_urls')),
    # # profile endpoint(s)
    # path('api/v1/user/', include('apps.users.urls.profile_urls')),
    # # path('api/v1/portfolio/', include('apps.portfolios.urls')),
    # # path('api/v1/schemas/', include('schemas.urls')),
    # # path('api/v1/', include('common.urls')),
    # # path('api/v1/accounts/', include('accounts.urls')),

]
