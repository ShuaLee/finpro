from django.contrib import admin
from .models import Stock, CustomStock

# Register your models here.


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'currency', 'price',
                    'pe_ratio', 'quote_type', 'dividend_yield', 'sector', 'last_updated')
    search_fields = ('ticker',)
    actions = ['refresh_fmp_data']

    readonly_fields = (
        'name', 'currency', 'price',
        'average_volume', 'volume', 'pe_ratio', 'dividend_yield', 'sector', 'industry',
        'last_updated',
    )

    fieldsets = (
        ('Basic Info', {
            'fields': ('ticker',)
        }),
        ('Company Data', {
            'fields': ('name', 'quote_type', 'sector', 'industry')
        }),
        ('Price Data', {
            'fields': ('price', 'currency')
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
        if not change: # New stock
            ticker = form.cleaned_data['ticker'].upper()
            # check for duplicates
            if Stock.objects.filter(ticker=ticker).exists() or CustomStock.objects.filter(ticker=ticker).exists():
                self.message_user(request, f"Ticker {ticker} already exists.", level='error')
                return
            # Try creating Stock
            stock = Stock.create_from_ticker(ticker)
            if stock:
                obj = stock
                self.message_user(request, f"Created Stock for {ticker} with FMP data.")
            else:
                # Create CustomStock if invalid
                obj = CustomStock(ticker=ticker)
                obj.save()
                self.message_user(request, f"Ticker {ticker} not found in FMP, created as CustomStock.")
        else:
            super().save_model(request, obj, form, change)

    def refresh_fmp_data(self, request, queryset):
        if queryset.exists():
            updated, failed, invalid = Stock.bulk_update_from_fmp(stocks=queryset)
            self.message_user(
                request,
                f"Refreshed {updated} selected stocks, {failed} failed, {invalid} invalid tickers."
            )
        else:
            updated, failed, invalid = Stock.bulk_update_from_fmp()
            self.message_user(
                request,
                f"Refreshed {updated} stocks, {failed} failed, {invalid} invalid tickers."
            )
    refresh_fmp_data.short_description = "Refresh selected stocks from FMP"

@admin.register(CustomStock)
class CustomStockAdmin(admin.ModelAdmin):
    list_display = ('ticker',)
    search_fields = ('ticker',)

    def save_model(self, request, obj, form, change):
        ticker = form.cleaned_data['ticker'].upper()
        if Stock.objects.filter(ticker=ticker).exists():
            self.message_user(request, f"Ticker {ticker} exists as a Stock.", level='error')
            return
        if not change and CustomStock.objects.filter(ticker=ticker).exists():
            self.message_user(request, f"Ticker {ticker} already exists as a CustomStock.", level='error')
            return
        super().save_model(request, obj, form, change)