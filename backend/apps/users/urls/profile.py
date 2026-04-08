from django.urls import path

from apps.users.views import ProfileOptionsView, ProfileView


urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile-detail"),
    path("profile/options/", ProfileOptionsView.as_view(), name="profile-options"),
]
