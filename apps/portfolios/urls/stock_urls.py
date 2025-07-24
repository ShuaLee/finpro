from django.urls import path
from portfolios.views.stock import StockPortfolioCreateView

urlpatterns = [
    path('', StockPortfolioCreateView.as_view(), name='create-stock-portfolio'),
    # path('dashboard/', StockPortfolioDashboardView.as_view(), name='stock-portfolio-dashboard'),
]
