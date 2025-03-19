from django.urls import path
from .views import ProfileViewSet
from portfolio.views import PortfolioViewSet
from securities.views import SelfManagedAccountViewSet


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
    path('profile/portfolio/stock-accounts/add-self-managed-account/', PortfolioViewSet.as_view(
        {'post': 'add_self_managed_account'}), name='add-self-managed-account'),
]
