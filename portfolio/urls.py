from django.urls import path, include
from .views import PortfolioDetailView


urlpatterns = [
    path('', PortfolioDetailView.as_view(), name='portfolio-detail'),
    path('stock-portfolio/', include('stock_portfolio.urls')),
]