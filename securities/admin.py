from django.contrib import admin
from .models import Stock, StockAccount, StockTag, StockHolding


class StockTagInline(admin.TabularInline):
    model = StockTag
    fk_name = 'parent'
    extra = 1  # Number of empty forms to show for creating new tags


@admin.register(StockTag)
class StockTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_holding', 'parent')
    search_fields = ('name',)

    # Add the inline for managing sub-tags
    inlines = [StockTagInline]


# StockHolding Inline for StockAccount
class StockHoldingInline(admin.TabularInline):
    model = StockHolding
    extra = 1
    fields = ('stock', 'shares')


# StockAccount Admin
@admin.register(StockAccount)
class StockAccountAdmin(admin.ModelAdmin):
    list_display = ('account_type', 'account_name',
                    'portfolio', 'stock_count', 'created_at')
    search_fields = ('account_name',)
    list_filter = ('account_type',)
    inlines = [StockHoldingInline]

    def stock_count(self, obj):
        return obj.stocks.count()
    stock_count.short_description = "Stocks Owned"

# Stock Admin


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'account_count')
    search_fields = ('ticker',)
    ordering = ('ticker',)

    def account_count(self, obj):
        return obj.stock_accounts.count()
    account_count.short_description = "Accounts Holding"

# StockHolding Admin (optional, for direct access)


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = ('stock', 'stock_account', 'shares')
    search_fields = ('stock__ticker', 'stock_account__account_name')
    list_filter = ('stock_account__portfolio',)
