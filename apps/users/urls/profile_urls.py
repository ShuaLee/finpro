"""
users.urls.profile_urls
~~~~~~~~~~~~~~~~~~~~~~~
Defines URL patterns for user profile-related endpoints:
- Profile retrieval
- Profile updates (PUT/PATCH)
"""

from django.urls import path
from users.views import ProfileView, ProfilePlanUpdateView

urlpatterns = [
    # Profile management for authenticated users
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('profile/plan/', ProfilePlanUpdateView.as_view(),
         name='update-profile-plan'),
]
