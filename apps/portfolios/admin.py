"""
Portfolio Admin Configuration
-----------------------------

Provides Django admin configurations for:
- Portfolio
- StockPortfolio
- MetalPortfolio

Features:
- Search by user email for quick lookup.
- Display key fields for clarity.
"""

from django.contrib import admin
from portfolios.models.portfolio import Portfolio
from portfolios.models.stock import StockPortfolio
from portfolios.models.metal import MetalPortfolio


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """
    Admin configuration for the main Portfolio model.
    """
    list_display = ['profile', 'created_at']
    search_fields = ['profile__user__email']
    list_filter = ['created_at']


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    """
    Admin configuration for StockPortfolio.
    """
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']
    list_filter = ['created_at']


@admin.register(MetalPortfolio)
class MetalPortfolioAdmin(admin.ModelAdmin):
    """
    Admin configuration for MetalPortfolio.
    """
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']
    list_filter = ['created_at']
