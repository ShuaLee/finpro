from django.contrib import admin
from portfolios.models.stock import StockPortfolio
from schemas.services.schema import initialize_stock_schema


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "portfolio")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # Only on create
            initialize_stock_schema(obj)
