from django.contrib import admin
from .models import Portfolio
# from securities.models import StockPortfolio


"""
class StockPortfolioInline(admin.TabularInline):
    model = StockPortfolio
    extra = 1
"""

@admin.register(Portfolio)
class IndividualPortfolioAdmin(admin.ModelAdmin):
    list_display = ['profile', 'created_at',]
    # inlines = [StockPortfolioInline]
