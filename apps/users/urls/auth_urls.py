from django.urls import path
from ..views import (
    SignupCompleteView, CookieLoginView, CookieLogoutView,
    CookieRefreshView, auth_status
)

urlpatterns = [
    path('signup-complete/', SignupCompleteView.as_view(), name='signup-complete'),
    path('login/', CookieLoginView.as_view(), name='cookie-login'),
    path('logout/', CookieLogoutView.as_view(), name='cookie-logout'),
    path('refresh/', CookieRefreshView.as_view(), name="cookie-refresh"),
    path('status/', auth_status, name="auth-status"),
]