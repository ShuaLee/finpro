from django.urls import path, include
from .views import ProfileViewSet

urlpatterns = [
    path('', ProfileViewSet.as_view(
        {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='profile-detail'),
]
