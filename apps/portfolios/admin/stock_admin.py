from django.contrib import admin
from portfolios.models import StockPortfolio


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    """
    Admin for the StockPortfolio model.
    """
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']
    list_filter = ['created_at']
