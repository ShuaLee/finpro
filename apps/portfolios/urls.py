"""
Portfolio App URLs
-------------------

Defines API routes for the main Portfolio and asset-specific portfolios.
"""

from django.urls import path
from apps.portfolios.views.portfolio import PortfolioCreateView, PortfolioDetailView
from apps.portfolios.views.stock import StockPortfolioCreateView, StockPortfolioDashboardView
from apps.portfolios.views.metal import MetalPortfolioCreateView

urlpatterns = [
    # Main Portfolio
    path('', PortfolioCreateView.as_view(), name='create-portfolio'),       # POST
    path('me/', PortfolioDetailView.as_view(), name='portfolio-detail'),    # GET

    # Stock Portfolio
    path('stocks/', StockPortfolioCreateView.as_view(), name='create-stock-portfolio'),
    path('stocks/dashboard/', StockPortfolioDashboardView.as_view(), name='stock-portfolio-dashboard'),

    # Metal Portfolio
    path('metals/', MetalPortfolioCreateView.as_view(), name='create-metal-portfolio'),
]