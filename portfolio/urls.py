from django.urls import path
from .views import PortfolioDetailView


urlpatterns = [
    path('', PortfolioDetailView.as_view(), name='portfolio-detail'),
]