from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import path
from .views import ProfileViewSet
from portfolio.views import PortfolioViewSet
from securities.views import StockAccountViewSet, StockPortfolioViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

# Nested router for endpoints under profiles
profile_router = routers.NestedDefaultRouter(
    router, r'profiles', lookup='profile'
)

# Register portfolio as a single endpoint (no PK)
profile_router.register(
    r'portfolio', PortfolioViewSet, basename='profile-portfolio'
)

urlpatterns = router.urls + profile_router.urls


"""
portfolio_router = routers.NestedDefaultRouter(
    profile_router, r'portfolio', lookup='portfolio'
)
portfolio_router.register(
    r'stockportfolio', StockPortfolioViewSet, basename='portfolio-stockportfolio'
)

# Nested router for stockaccounts under stockportfolio
stockportfolio_router = routers.NestedDefaultRouter(
    portfolio_router, r'stockportfolio', lookup='stockportfolio'
)
stockportfolio_router.register(
    r'stockaccounts', StockAccountViewSet, basename='stockportfolio-stockaccounts'
)

urlpatterns = router.urls + profile_router.urls + \
    portfolio_router.urls + stockportfolio_router.urls

"""
# Nested router for stockportfolio under portfolio
