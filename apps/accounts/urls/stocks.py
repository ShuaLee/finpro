from django.urls import path
from rest_framework.routers import DefaultRouter
from ..views.stocks import SelfManagedAccountViewSet, ManagedAccountViewSet

router = DefaultRouter()
router.register(r'self-managed-accounts',
                SelfManagedAccountViewSet, basename='self-managed-accounts')
router.register(r'managed-accounts', ManagedAccountViewSet,
                basename='managed-accounts')

urlpatterns = router.urls
