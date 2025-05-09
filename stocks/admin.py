from django.contrib import admin
from .models import Stock

# Register your models here.


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'is_custom', 'currency', 'quote_type', 'exchange',
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

    def save_model(self, request, obj, form, change):
        if not change:  # New stock
            obj = Stock.create_from_ticker(form.cleaned_data['ticker'])
        else:
            super().save_model(request, obj, form, change)

    def refresh_yfinance_data(self, request, queryset):
        updated, failed, invalid = Stock.bulk_update_from_yfinance(list(queryset))
        self.message_user(
            request, f"{updated} stocks refreshed, {failed} failed, {invalid} invalid tickers."
        )

    refresh_yfinance_data.short_description = "Refresh selected stocks from yfinance."