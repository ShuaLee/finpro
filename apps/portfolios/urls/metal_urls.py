from django.urls import path
from portfolios.views.metal import MetalPortfolioCreateView

urlpatterns = [
    path('', MetalPortfolioCreateView.as_view(), name='create-metal-portfolio'),
]
