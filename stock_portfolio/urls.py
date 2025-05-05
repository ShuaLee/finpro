from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockPortfolioDetailView, SelfManagedAccountViewSet

router = DefaultRouter()
router.register(
    r'self-managed-accounts',
    SelfManagedAccountViewSet,
    basename='self-managed-account'
)

urlpatterns = [
    path('', StockPortfolioDetailView.as_view(), name='stock-portfolio-detail'),
    path('', include(router.urls)),
]