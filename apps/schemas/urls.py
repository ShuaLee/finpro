from django.urls import path, include
from rest_framework.routers import DefaultRouter
from schemas.views import (
    SchemaViewSet,
    SchemaColumnValueViewSet,
    SchemaColumnVisibilityToggleViewSet,
    SchemaHoldingsView,
)

router = DefaultRouter()
router.register(r'schemas', SchemaViewSet, basename='schema')
router.register(r'schema-values', SchemaColumnValueViewSet,
                basename='schema-value')

# Custom action not supported via DefaultRouter
schema_visibility = SchemaColumnVisibilityToggleViewSet.as_view({
    'post': 'toggle'
})

urlpatterns = [
    path('', include(router.urls)),
    path('stocks/accounts/<int:account_id>/view/',
         SchemaHoldingsView.as_view(), name='stock-schema-holdings'),
    path('columns/visibility/toggle/', schema_visibility,
         name='schema-column-visibility-toggle'),
]
