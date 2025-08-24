from django.contrib import admin
from portfolios.models import MetalPortfolio
from portfolios.admin.base import BaseSubPortfolioAdmin


@admin.register(MetalPortfolio)
class MetalPortfolioAdmin(BaseSubPortfolioAdmin):
    schema_type = "metal"
    account_model_key = "metal"
