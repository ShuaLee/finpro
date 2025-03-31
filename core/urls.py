from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet
from portfolio.views import PortfolioViewSet
from securities.views import SelfManagedAccountViewSet, StockPortfolioViewSet


urlpatterns = [
    # Profile endpoint (returns logged-in user's profile)
    path('profile/', ProfileViewSet.as_view(
        {'get': 'retrieve', 'put': 'update'}), name='profile-detail'),

    # Portfolio endpoint (general portfolio info)
    path('profile/portfolio/',
         PortfolioViewSet.as_view({'get': 'retrieve'}), name='portfolio-detail'),

    # Stock Portfolio endpoint (portfolio details)
    path('profile/portfolio/stock-portfolio/',
         StockPortfolioViewSet.as_view({'get': 'retrieve', 'patch': 'update'}), name='stock-portfolio-detail'),
    path('profile/portfolio/stock-portfolio/add-self-managed-account/',
         StockPortfolioViewSet.as_view({'post': 'add_self_managed_account'}), name='stock-portfolio-add-self-managed-account'),
    # Future: path('profile/portfolio/stock-portfolio/add-managed-account/', ...),

    # All Stock Accounts endpoint
    path('profile/portfolio/stock-portfolio/stock-accounts/',
         StockPortfolioViewSet.as_view({'get': 'list'}), name='stock-accounts-list'),

    # Self Managed Accounts endpoints
    path('profile/portfolio/stock-portfolio/self-managed-accounts/', SelfManagedAccountViewSet.as_view(
        {'get': 'list', 'post': 'create'}), name='self-managed-accounts-list'),
    path('profile/portfolio/stock-portfolio/self-managed-accounts/<int:pk>/',
         SelfManagedAccountViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='self-managed-accounts-detail'),
    path('profile/portfolio/stock-portfolio/self-managed-accounts/<int:pk>/add-stock/',
         SelfManagedAccountViewSet.as_view({'post': 'add_stock'}), name='self-managed-accounts-add-stock'),
    path('profile/portfolio/stock-portfolio/self-managed-accounts/<int:pk>/update-stock/<int:holding_pk>/',
         SelfManagedAccountViewSet.as_view({'patch': 'update_stock'}), name='self-managed-accounts-update-stock'),
    path('profile/portfolio/stock-portfolio/self-managed-accounts/<int:pk>/reset-stock-column/<int:holding_pk>/',
         SelfManagedAccountViewSet.as_view({'post': 'reset_stock_column'}), name='self-managed-accounts-reset-stock-column'),

    # Managed Accounts endpoints (placeholder for future)
    # path('profile/portfolio/stock-portfolio/managed-accounts/', ManagedAccountViewSet.as_view(...)),
    # path('profile/portfolio/stock-portfolio/managed-accounts/<int:pk>/', ManagedAccountViewSet.as_view(...)),
]

"""
urlpatterns = [
    # Profile endpoints
    path('profile/', ProfileViewSet.as_view(
        {'get': 'retrieve', 'put': 'update'}), name='profile-detail'),

    # Portfolio endpoints
    path('profile/portfolio/',
         PortfolioViewSet.as_view({'get': 'retrieve'}), name='portfolio-detail'),
    path('profile/portfolio/stock-accounts/', SelfManagedAccountViewSet.as_view(
        {'get': 'list', 'post': 'create'}), name='stock-accounts-list'),
    path('profile/portfolio/stock-accounts/<int:pk>/',
         SelfManagedAccountViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='stock-accounts-detail'),
    path('profile/portfolio/stock-accounts/<int:pk>/add-stock/',
         SelfManagedAccountViewSet.as_view({'post': 'add_stock'}), name='stock-accounts-add-stock'),
    path('profile/portfolio/stock-accounts/add-self-managed-account/', PortfolioViewSet.as_view(
        {'post': 'add_self_managed_account'}), name='add-self-managed-account'),
]
"""
