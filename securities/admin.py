from django.contrib import admin
from .models import Stock, StockAccount, StockTag


class StockTagInline(admin.TabularInline):
    model = StockTag
    fk_name = 'parent'
    extra = 1  # Number of empty forms to show for creating new tags


@admin.register(StockTag)
class StockTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_account', 'parent')
    search_fields = ('name',)

    # Add the inline for managing sub-tags
    inlines = [StockTagInline]

# StockAccount Admin


@admin.register(StockAccount)
class StockAccountAdmin(admin.ModelAdmin):
    list_display = ('account_type', 'account_name', 'portfolio', 'created_at')
    search_fields = ('account_name',)
    list_filter = ('account_type',)

# Stock Admin


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'exchange',
                    'current_price', 'stock_type', 'last_updated')
    search_fields = ('ticker', 'name', 'sector', 'country')
    list_filter = ('stock_type', 'sector', 'country')
    ordering = ('ticker',)
