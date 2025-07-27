from django.urls import path, include
from rest_framework.routers import DefaultRouter
from schemas.views.stocks.schemas import StockSchemaViewSet
from schemas.views.stocks.value import StockSCVEditView

router = DefaultRouter()
# Empty because prefix handled by include
router.register(r'', StockSchemaViewSet, basename='stock-schema')

urlpatterns = [
    path('', include(router.urls)),
    path('scv/<int:pk>/edit/', StockSCVEditView.as_view(), name='stock-scv-edit'),
]
