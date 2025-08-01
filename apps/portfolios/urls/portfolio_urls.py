from django.urls import path, include
from portfolios.views.portfolio import PortfolioDetailView


urlpatterns = [
    path('', PortfolioDetailView.as_view(), name='portfolio-detail'),
    path('stocks/', include('portfolios.urls.stock_urls')),
]
