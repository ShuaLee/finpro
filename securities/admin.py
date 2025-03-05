from django.contrib import admin
from .models import StockAccount

# Register your models here.


@admin.register(StockAccount)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ('account_type', 'account_name', 'portfolio')
    search_fields = ('account_name',)
