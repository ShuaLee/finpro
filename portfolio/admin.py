from django.contrib import admin
from .models import IndividualPortfolio
from securities.models import StockPortfolio
# Register your models here.


class StockPortfolioInline(admin.TabularInline):
    model = StockPortfolio
    extra = 1


@admin.register(IndividualPortfolio)
class IndividualPortfolioAdmin(admin.ModelAdmin):
    list_display = ['profile', 'created_at',]
    inlines = [StockPortfolioInline]
