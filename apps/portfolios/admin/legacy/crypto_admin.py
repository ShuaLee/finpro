from django.contrib import admin
from portfolios.models import CryptoPortfolio
from portfolios.admin.base import BaseSubPortfolioAdmin


@admin.register(CryptoPortfolio)
class CryptoPortfolioAdmin(BaseSubPortfolioAdmin):
    schema_type = "crypto"
    account_model_key = "crypto"
