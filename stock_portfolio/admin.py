from django import forms
from django.contrib import admin
from .constants import PREDEFINED_COLUMNS
from .models import StockPortfolio, SelfManagedAccount, ManagedAccount, Stock, StockHolding, Schema, SchemaColumn, SchemaColumnValue


class SchemaColumnForm(forms.ModelForm):
    predefined_choice = forms.ChoiceField(
        choices=[('', 'Select a column…')] + [
            (f"{source}:{item['field']}",
             f"{source.title()}: {item['label']} ({item['type']})")
            for source, items in PREDEFINED_COLUMNS.items()
            for item in items
        ] + [('custom', 'Custom')],
        required=False,
        label="Predefined Column"
    )

    class Meta:
        model = SchemaColumn
        fields = ['schema', 'predefined_choice', 'name',
                  'data_type', 'source', 'source_field']

    def clean(self):
        cleaned_data = super().clean()
        choice = cleaned_data.get('predefined_choice')

        if choice and choice != 'custom':
            try:
                source, field = choice.split(':')
                column = next(
                    item for item in PREDEFINED_COLUMNS[source] if item['field'] == field)
            except (ValueError, KeyError, StopIteration):
                raise forms.ValidationError(
                    "Invalid predefined column selected.")

            cleaned_data['source'] = source
            cleaned_data['source_field'] = column['field']
            cleaned_data['data_type'] = column['type']
            cleaned_data['name'] = column['label']

        elif not all([cleaned_data.get('name'), cleaned_data.get('data_type'), cleaned_data.get('source')]):
            raise forms.ValidationError(
                "For a custom column, all fields must be filled out manually.")

        return cleaned_data


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

    def refresh_yfinance_data(self, request, queryset):
        updated = 0
        for stock in queryset:
            if stock.fetch_yfinance_data(force_update=True):
                stock.is_custom = not any([
                    stock.short_name,
                    stock.long_name,
                    stock.exchange
                ])
                stock.save()
                updated += 1
        self.message_user(
            request, f"{updated} stocks refreshed and custom status updated.")

    refresh_yfinance_data.short_description = "Refresh selected stocks from yfinance."


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = ['stock', 'stock_account', 'shares', 'purchase_price']
    list_filter = ['stock_account__stock_portfolio']


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ['stock_portfolio', 'name', 'created_at']


@admin.register(SchemaColumn)
class SchemaColumn(admin.ModelAdmin):
    list_display = ['schema', 'name', 'data_type', 'source', 'source_field']
    form = SchemaColumnForm


@admin.register(SchemaColumnValue)
class SchemaColumnValue(admin.ModelAdmin):
    list_display = ['stock_holding', 'column', 'value']
