from django.urls import path
from .views import SchemaView

urlpatterns = [
    path('<int:schema_id>/', SchemaView.as_view(), name='schema'),
]