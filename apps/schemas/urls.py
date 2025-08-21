# # urls.py
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from schemas.views import (
#     SchemaViewSet,
#     SchemaColumnViewSet,
#     SchemaColumnValueViewSet,
#     SchemaColumnVisibilityToggleViewSet,
#     SchemaHoldingsView,
#     SchemaAvailableColumnsView,
#     SchemaFormulaVariableListView
# )

# router = DefaultRouter()
# router.register(r'schemas', SchemaViewSet)
# router.register(r'columns', SchemaColumnViewSet)
# router.register(r'column-values', SchemaColumnValueViewSet)

# schema_visibility = SchemaColumnVisibilityToggleViewSet.as_view({
#     'post': 'toggle'
# })

# urlpatterns = [
#     path('', include(router.urls)),
#     path('stocks/accounts/<int:account_id>/view/',
#          SchemaHoldingsView.as_view(), name='stock-schema-holdings'),
#     path('columns/visibility/toggle/', schema_visibility,
#          name='schema-column-visibility-toggle'),
#     path('schemas/<int:schema_id>/available-columns/', SchemaAvailableColumnsView.as_view(), name='schema-available-columns'),
#     path('schemas/<int:schema_id>/formula-variables/', SchemaFormulaVariableListView.as_view(), name='schema-formula-variables'),
# ]
