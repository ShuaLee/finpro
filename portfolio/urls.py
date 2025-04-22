from django.urls import path, include


urlpatterns = [
    # path('', PortfolioSummaryView.as_view(), name='portfolio-summary'),
    path('stock-holdings/', include('stock_portfolio.urls')),
]