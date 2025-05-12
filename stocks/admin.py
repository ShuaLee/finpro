from django.contrib import admin
from .models import Stock

# Register your models here.


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'is_custom', 'short_name', 'price',
                    'pe_ratio', 'quote_type', 'sector', 'last_updated')
    search_fields = ('ticker',)
    actions = ['refresh_fmp_data']

    readonly_fields = (
        'short_name', 'long_name', 'price',
        'average_volume', 'volume', 'pe_ratio', 'quote_type', 'sector', 'industry',
        'last_updated',
    )

    fieldsets = (
        ('Basic Info', {
            'fields': ('ticker',)
        }),
        ('Company Data', {
            'fields': ('short_name', 'long_name', 'quote_type', 'sector', 'industry')
        }),
        ('Price Data', {
            'fields': ('price',)
        }),
        ('Volume', {
            'fields': ('average_volume', 'volume')
        }),
        ('Valuation', {
            'fields': ('pe_ratio',)
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

    def refresh_fmp_data(self, request, queryset):
        updated, failed, invalid = Stock.bulk_update_batch(list(queryset))
        self.message_user(
            request, f"{updated} stocks refreshed, {failed} failed, {invalid} invalid tickers."
        )

    refresh_fmp_data.short_description = "Refresh selected stocks from FMP."
