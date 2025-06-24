from django.urls import path
from .views import StockPortfolioDashboardView



urlpatterns = [
    path('stock-portfolio/', StockPortfolioDashboardView.as_view(), name='stock-portfolio-dashboard'),
]