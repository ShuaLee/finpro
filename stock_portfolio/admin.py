from django.contrib import admin
from .models import StockPortfolio, SelfManagedAccount, ManagedAccount, Stock, StockHolding

@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']

@admin.register(SelfManagedAccount)
class SelfManagedAccountAdmin(admin.ModelAdmin):
    list_display = ['stock_portfolio', 'name', 'created_at']

@admin.register(ManagedAccount)
class ManagedAccountAdmin(admin.ModelAdmin):
    list_display = ['stock_portfolio', 'name', 'created_at']

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'currency', 'quote_type', 'exchange',
                    'dividend_rate', 'last_price', 'last_updated')
    list_filter = ('exchange',)
    search_fields = ('ticker',)
    actions = ['refresh_yfinance_data']

    readonly_fields = (
        'short_name', 'long_name', 'currency', 'exchange', 'quote_type', 'market',
        'last_price', 'previous_close', 'open_price', 'day_high', 'day_low',
        'fifty_two_week_high', 'fifty_two_week_low',
        'average_volume', 'average_volume_10d', 'volume',
        'market_cap', 'beta', 'pe_ratio', 'forward_pe', 'price_to_book',
        'dividend_rate', 'dividend_yield', 'payout_ratio', 'ex_dividend_date',
        'sector', 'industry', 'website', 'full_time_employees', 'long_business_summary',
        'last_updated',
    )

    fieldsets = (
        ('Basic Info', {
            'fields': ('ticker',)
        }),
        ('Price Data', {
            'fields': ('last_price', 'previous_close', 'open_price', 'day_high', 'day_low')
        }),
        ('52-Week Range', {
            'fields': ('fifty_two_week_high', 'fifty_two_week_low')
        }),
        ('Volume', {
            'fields': ('average_volume', 'average_volume_10d', 'volume')
        }),
        ('Valuation', {
            'fields': ('market_cap', 'beta', 'pe_ratio', 'forward_pe', 'price_to_book')
        }),
        ('Dividends', {
            'fields': ('dividend_rate', 'dividend_yield', 'payout_ratio', 'ex_dividend_date')
        }),
        ('Company Profile', {
            'fields': ('short_name', 'long_name', 'currency', 'exchange', 'quote_type', 'market',
                       'sector', 'industry', 'website', 'full_time_employees', 'long_business_summary')
        }),
        ('Timestamps', {
            'fields': ('last_updated',)
        }),
    )

    def refresh_yfinance_data(self, request, queryset):
        for stock in queryset:
            stock.fetch_yfinance_data(force_update=True)
        self.message_user(request, "Selected stocks have been refreshed from yfinance.")
    refresh_yfinance_data.short_description = "Refresh selected stocks from yfinance."

@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = ['stock', 'stock_account', 'shares', 'purchase_price']
    list_filter = ['stock_account__stock_portfolio']