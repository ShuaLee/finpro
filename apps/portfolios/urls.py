from django.urls import path, include
from .views import StockPortfolioDashboardView, PortfolioDetailView


urlpatterns = [
    path('stock-portfolio/', StockPortfolioDashboardView.as_view(),
         name='stock-portfolio-dashboard'),
    path('stock-portfolio/', include('accounts.urls.stocks')),
    path('stock-portfolio/schemas/', include('schemas.urls')),
    path('portfolio/', PortfolioDetailView.as_view(), name='profile'),
]
