from django.urls import path
from common.views.metadata import metadata_view

urlpatterns = [
    path('metadata/', metadata_view, name='metadata'),
]
