"""
from django.contrib import admin
from portfolios.models.stock import StockPortfolio
from accounts.config.account_model_registry import get_account_model_map
from schemas.services.schema_initialization import initialize_asset_schema


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "portfolio")
    search_fields = ["portfolio__profile__user__email"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # Only on create
            account_model_map = get_account_model_map("stock")
            initialize_asset_schema(
                subportfolio=obj,
                schema_type="stock",
                account_model_map=account_model_map,
            )
"""
