from django.contrib import admin
from .models.stocks import StockPortfolio

@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']
