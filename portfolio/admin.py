from django.contrib import admin
from .models import IndividualPortfolio
from securities.models import StockAccount
# Register your models here.


class StockPortfolioInline(admin.StackedInline):
    model = StockAccount
    extra = 0
    fields = ('account_type', 'account_name')


@admin.register(IndividualPortfolio)
class IndividualPortfolioAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'created_at')
    search_fields = ('profile__user__email', 'name')
    inlines = [StockPortfolioInline]
