from django.urls import path
from common.views.metadata import preferences_metadata_view

urlpatterns = [
    path('metadata/', preferences_metadata_view, name='metadata'),
]
