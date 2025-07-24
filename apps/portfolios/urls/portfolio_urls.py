from django.urls import path
from portfolios.views.portfolio import PortfolioCreateView, PortfolioDetailView

urlpatterns = [
    path('', PortfolioCreateView.as_view(), name='create-portfolio'),
    path('me/', PortfolioDetailView.as_view(), name='portfolio-detail'),
]
