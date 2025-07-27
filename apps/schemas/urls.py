from django.urls import path
from schemas.views.schemas import (
    SchemaDetailView,
    AddCustomColumnView,
    AddCalculatedColumnView,
    UpdateColumnValueView
)

urlpatterns = [
    path('<int:pk>/', SchemaDetailView.as_view(), name='schema-detail'),
    path('<int:schema_id>/columns/',
         AddCustomColumnView.as_view(), name='schema-add-column'),
    path('<int:schema_id>/calculated-columns/',
         AddCalculatedColumnView.as_view(), name='schema-add-calculated'),
    path('values/<int:pk>/', UpdateColumnValueView.as_view(),
         name='schema-value-update'),
]
