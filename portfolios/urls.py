from django.urls import path, include
from .views import StockPortfolioDashboardView


urlpatterns = [
    path('stock-portfolio/', StockPortfolioDashboardView.as_view(),
         name='stock-portfolio-dashboard'),
    path('stock-portfolio/', include('accounts.urls.stocks'))
]
