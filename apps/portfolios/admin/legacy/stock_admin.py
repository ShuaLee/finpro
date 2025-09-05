from django.contrib import admin
from portfolios.models import StockPortfolio
from portfolios.admin.base import BaseSubPortfolioAdmin


@admin.register(StockPortfolio)
class StockPortfolioAdmin(BaseSubPortfolioAdmin):
    schema_type = "stock"
    account_model_key = "stock"
