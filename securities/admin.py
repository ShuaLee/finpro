from django.contrib import admin
from .models import Stock, StockHolding, StockPortfolio


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ['get_user_email', 'created_at']

    # Fields to search by
    search_fields = ['portfolio__profile__user__email']

    # Fields to filter by
    list_filter = ['created_at']

    # Make these fields read-only in the detail view
    readonly_fields = ['portfolio', 'created_at']

    # Custom method for list_display
    def get_user_email(self, obj):
        return obj.portfolio.profile.user.email
    get_user_email.short_description = "User Email"


# StockHolding Inline for StockAccount
class StockHoldingInline(admin.TabularInline):
    model = StockHolding
    extra = 1
    fields = ('stock', 'shares')


"""
# StockAccount Admin
@admin.register(StockAccount)
class StockAccountAdmin(admin.ModelAdmin):
    # Changed 'portfolio' to 'stock_portfolio'
    list_display = ['account_name', 'account_type',
                    'stock_portfolio', 'created_at']
    list_filter = ['account_type', 'stock_portfolio']  # Updated
    search_fields = ['account_name', 'stock_portfolio__name']
"""
# Stock Admin


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'currency', 'is_etf', 'exchange',
                    'dividend_rate', 'last_price', 'last_updated')
    list_filter = ('is_etf', 'exchange')
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
        'last_updated', 'is_etf'
    )

    fieldsets = (
        ('Basic Info', {
            'fields': ('ticker', 'is_etf')
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
        self.message_user(
            request, "Selected stocks have been refreshed from yfinance.")
    refresh_yfinance_data.short_description = "Refresh selected stocks from yfinance"

# StockHolding Admin (optional, for direct access)


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = ['stock', 'stock_account', 'shares', 'purchase_price']
    # Updated to new relationship
    list_filter = ['stock_account__stock_portfolio']
