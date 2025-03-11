from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import path
from .views import ProfileViewSet
from portfolio.views import IndividualPortfolioViewSet
from securities.views import StockAccountViewSet, StockPortfolioViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

# Nested router for portfolios under profiles
profile_router = routers.NestedDefaultRouter(
    router, r'profiles', lookup='profile'
)
profile_router.register(
    r'portfolio', IndividualPortfolioViewSet, basename='profile-portfolio'
)

# Nested router for stockportfolios under portfolios
portfolio_router = routers.NestedDefaultRouter(
    profile_router, r'portfolio', lookup='portfolio'
)
portfolio_router.register(
    r'stockportfolios', StockPortfolioViewSet, basename='portfolio-stockportfolios'
)

# Nested router for stockaccounts under stockportfolios
stockportfolio_router = routers.NestedDefaultRouter(
    portfolio_router, r'stockportfolios', lookup='stock_portfolio'
)
stockportfolio_router.register(
    r'stockaccounts', StockAccountViewSet, basename='stockportfolio-stockaccounts'
)

urlpatterns = router.urls + profile_router.urls + \
    portfolio_router.urls + stockportfolio_router.urls
