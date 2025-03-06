from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import path
from .views import ProfileViewSet
from portfolio.views import IndividualPortfolioViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

# Create a nested router for portfolios under the profiles endpoint
profile_router = routers.NestedDefaultRouter(
    router, r'profiles', lookup='profile')
profile_router.register(
    r'portfolio', IndividualPortfolioViewSet, basename='profile-portfolio')


urlpatterns = router.urls + profile_router.urls
