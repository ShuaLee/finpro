from django.urls import path
from accounts.views.metals import StorageFacilityListCreateView

urlpatterns = [
    path('storage/', StorageFacilityListCreateView.as_view(), name='storage-facility'),
]
