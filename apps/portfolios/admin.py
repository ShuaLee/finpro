from django.contrib import admin
from .models.metals import MetalPortfolio
from .models.stocks import StockPortfolio
from .models.portfolio import Portfolio

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['profile', 'created_at',]
    # inlines = [StockPortfolioInline]

@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']

@admin.register(MetalPortfolio)
class MetalPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']

