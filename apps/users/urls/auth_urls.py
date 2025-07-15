"""
users.urls.auth_urls
~~~~~~~~~~~~~~~~~~~~
Defines URL patterns for authentication-related endpoints:
- Signup
- Login/Logout
- Token Refresh
- Auth Status
"""


from django.urls import path
from ..views import (
    SignupView, CookieLoginView, CookieLogoutView,
    CookieRefreshView, auth_status
)

urlpatterns = [
    # User signup completion (open to all)
    path('signup/', SignupView.as_view(), name='signup'),

    # Cookie-based authentication endpoints
    path('login/', CookieLoginView.as_view(), name='cookie-login'),
    path('logout/', CookieLogoutView.as_view(), name='cookie-logout'),
    path('refresh/', CookieRefreshView.as_view(), name="cookie-refresh"),

    # Check authentication status
    path('status/', auth_status, name="auth-status"),
]
