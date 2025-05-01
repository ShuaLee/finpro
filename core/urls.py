from django.urls import path, include
from .views import ProfileViewSet

urlpatterns = [
    # Profile endpoint (returns logged-in user's profile)
    path('profile/', ProfileViewSet.as_view({'get': 'retrieve', 'put': 'update'}), name='profile-detail'),
    path('profile/portfolio/', include('portfolio.urls')),
]
