from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import ProfileViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = router.urls
