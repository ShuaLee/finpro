from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import path
from .views import ProfileViewSet
from portfolio.views import IndividualPortfolioViewSet
from securities.views import StockAccountViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

# Nested router for portfolios under profiles
profile_router = routers.NestedDefaultRouter(
    router, r'profiles', lookup='profile')
profile_router.register(
    r'portfolio', IndividualPortfolioViewSet, basename='profile-portfolio')

# Nested router for stockaccounts under portfolios
portfolio_router = routers.NestedDefaultRouter(
    profile_router, r'portfolio', lookup='portfolio')
portfolio_router.register(
    r'stockaccounts', StockAccountViewSet, basename='portfolio-stockaccounts')

urlpatterns = router.urls + profile_router.urls + portfolio_router.urls
