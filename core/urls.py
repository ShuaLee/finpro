from django.urls import path, include
from .views import ProfileView, PortfolioDetailView, CookieLoginView, CookieLogoutView, CookieRefreshView


urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('portfolio/', PortfolioDetailView.as_view(), name='profile'),
    path('portfolio/', include('portfolios.urls')),
    path('auth/login/', CookieLoginView.as_view(), name='cookie-login'),
    path('auth/logout/', CookieLogoutView.as_view(), name='cookie-logout'),
    path("auth/refresh/", CookieRefreshView.as_view(), name="cookie-refresh"),
]
