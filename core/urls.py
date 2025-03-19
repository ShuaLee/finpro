from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import path, include
from .views import ProfileViewSet
from portfolio.views import PortfolioViewSet
from securities.views import StockPortfolioViewSet

"""
# Main router
router = DefaultRouter()

# Register profiles and portfolios, we use 'me' instead of nesting routes under profile_pk
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'portfolio', PortfolioViewSet, basename='portfolio')
router.register(r'stockportfolio', StockPortfolioViewSet,
                basename='stock-portfolio')
urlpatterns = [
    path('profile/', ProfileViewSet.as_view(
        {'get': 'retrieve', 'put': 'update'}), name='profile-detail'),
    path('portfolio/',
         PortfolioViewSet.as_view({'get': 'retrieve'}), name='portfolio-detail'),
    path('', include(router.urls)),
]
"""

urlpatterns = [
    path('profile/', ProfileViewSet.as_view(
        {'get': 'retrieve', 'put': 'update'}), name='profile-detail'),
    path('portfolio/',
         PortfolioViewSet.as_view({'get': 'retrieve'}), name='portfolio-detail'),
    path('portfolio/stock-accounts/', PortfolioViewSet.as_view(
        {'get': 'stock_portfolio'}), name='portfolio-stock-accounts'),
    path('portfolio/stock-accounts/add-self-managed-account/', PortfolioViewSet.as_view(
        {'post': 'add_self_managed_account'}), name='portfolio-add-self-managed-account'),
]
