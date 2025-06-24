from django.urls import path, include
from .views import ProfileView, PortfolioDetailView


urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('portfolio/', PortfolioDetailView.as_view(), name='profile'),
    path('portfolio/', include('portfolios.urls')),
]