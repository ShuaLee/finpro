from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockPortfolioDashboardView, SelfManagedAccountViewSet

router = DefaultRouter()
router.register(r'self-managed-accounts', SelfManagedAccountViewSet, basename='self-managed-accounts')

urlpatterns = [
    path('', StockPortfolioDashboardView.as_view(), name='stock-portfolio-dashboard'),
    path('', include(router.urls)),
]