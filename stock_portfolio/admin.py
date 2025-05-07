from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from .constants import PREDEFINED_COLUMNS, PREDEFINED_CALCULATED_COLUMNS
from .models import StockPortfolio, SelfManagedAccount, ManagedAccount, Stock, StockHolding, Schema, SchemaColumn, SchemaColumnValue


class StockPortfolioForm(forms.ModelForm):
    class Meta:
        model = StockPortfolio
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter default_schema choices to only schemas beloning to this portfolio
        if self.instance.pk:
            self.fields['default_self_managed_schema'].queryset = Schema.objects.filter(
                stock_portfolio=self.instance
            )
        else:
            self.fields['default_self_managed_schema'].queryset = Schema.objects.none()


class SchemaColumnForm(forms.ModelForm):
    predefined_choice = forms.ChoiceField(
        choices=[('', 'Select a column…')] + [
            (f"{source}:{item['field']}",
             f"{source.title()}: {item['label']} ({item['type']})")
            for source, items in PREDEFINED_COLUMNS.items()
            for item in items
        ] + [
            (f"calculated:{key}", f"Calculated: {key} ({val['type']})")
            for key, val in PREDEFINED_CALCULATED_COLUMNS.items()
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
                source, key = choice.split(':')
            except ValueError:
                raise forms.ValidationError(
                    "Invalid predefined column format.")

            if source in PREDEFINED_COLUMNS:
                column = next(
                    item for item in PREDEFINED_COLUMNS[source] if item['field'] == key)
                cleaned_data['source'] = source
                cleaned_data['source_field'] = column['field']
                cleaned_data['data_type'] = column['type']
                cleaned_data['name'] = column['label']

            elif source == 'calculated':
                column = PREDEFINED_CALCULATED_COLUMNS.get(key)
                if not column:
                    raise forms.ValidationError(
                        "Invalid calculated column selected.")
                cleaned_data['source'] = 'calculated'
                cleaned_data['source_field'] = column['formula']
                cleaned_data['data_type'] = column['type']
                cleaned_data['name'] = key

        elif not all([cleaned_data.get('name'), cleaned_data.get('data_type'), cleaned_data.get('source')]):
            raise forms.ValidationError(
                "For a custom column, all fields must be filled out manually.")

        return cleaned_data


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']
    form = StockPortfolioForm


@admin.register(SelfManagedAccount)
class SelfManagedAccountAdmin(admin.ModelAdmin):
    list_display = ['stock_portfolio', 'name', 'created_at', 'active_schema']
    list_filter = ('stock_portfolio', 'active_schema')

    def save_model(self, request, obj, form, change):
        if not obj.active_schema and obj.stock_portfolio.default_self_managed_schema:
            obj.active_schema = obj.stock_portfolio.default_self_managed_schema
        super().save_model(request, obj, form, change)


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

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            try:
                obj.delete()
            except ValidationError as e:
                self.message_user(
                    request,
                    f"Error deleting schema '{obj.name}': {e.messages[0]}",
                    level=messages.ERROR
                )

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)

        if request.method == "POST":
            try:
                obj.delete()
                self.message_user(
                    request, "The schema was deleted successfully.", level=messages.SUCCESS)
                return HttpResponseRedirect(reverse("admin:stock_portfolio_schema_changelist"))
            except ValidationError as e:
                self.message_user(
                    request, f"Error: {e.messages[0]}", level=messages.ERROR)
                return HttpResponseRedirect(reverse("admin:stock_portfolio_schema_change", args=[object_id]))

        return super().delete_view(request, object_id, extra_context)


@admin.register(SchemaColumn)
class SchemaColumn(admin.ModelAdmin):
    list_display = ['schema', 'name', 'data_type', 'source', 'source_field']
    form = SchemaColumnForm


@admin.register(SchemaColumnValue)
class SchemaColumnValue(admin.ModelAdmin):
    list_display = ['stock_holding', 'column', 'value']
