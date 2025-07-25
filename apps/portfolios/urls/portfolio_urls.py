from django.urls import path
from portfolios.views.portfolio import PortfolioDetailView

urlpatterns = [
    path('me/', PortfolioDetailView.as_view(), name='portfolio-detail'),
]
