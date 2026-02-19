from django.urls import path

from profiles.views import ProfileView, CompleteOnboardingView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile-detail"),
    path("profile/complete/", CompleteOnboardingView.as_view(), name="profile-complete"),
]
