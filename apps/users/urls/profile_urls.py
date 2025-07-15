"""
users.urls.profile_urls
~~~~~~~~~~~~~~~~~~~~~~~
Defines URL patterns for user profile-related endpoints:
- Profile retrieval
- Profile updates (PUT/PATCH)
"""

from django.urls import path
from users.views import ProfileView

urlpatterns = [
    # Profile management for authenticated users
    path('profile/', ProfileView.as_view(), name='user-profile'),
]
