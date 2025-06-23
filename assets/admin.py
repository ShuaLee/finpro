from django import forms
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from .models.stocks import Stock, StockHolding
import logging

logger = logging.getLogger(__name__)

# ------------------------------ Forms ---------------------------- #
class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = [
            'ticker', 'is_custom', 'price', 'name', 'currency', 'sector', 'industry',
            'dividend_yield', 'pe_ratio', 'quote_type', 'average_volume', 'volume'
        ]

    def clean(self):
        cleaned_data = super().clean()
        ticker = cleaned_data.get('ticker')
        is_custom = cleaned_data.get('is_custom')

        if ticker:
            ticker = ticker.upper()
            cleaned_data['ticker'] = ticker
            existing_stock = Stock.objects.filter(
                ticker=ticker).exclude(pk=self.instance.pk).first()
            if existing_stock:
                raise forms.ValidationError(f"Ticker {ticker} already exists.")

        return cleaned_data


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    form = StockForm
    list_display = ['ticker', 'name', 'is_custom',
                    'price', 'sector', 'last_updated']
    list_filter = ['is_custom', 'quote_type', 'sector', 'exchange']
    search_fields = ['ticker', 'name']
    list_per_page = 50
    fields = [
        'ticker', 'exchange', 'is_adr', 'is_custom', 'price', 'name', 'currency', 'sector', 'industry',
        'dividend_yield', 'pe_ratio', 'quote_type', 'average_volume', 'volume',
        'last_updated', 'created_at'
    ]
    readonly_fields = ['last_updated', 'created_at']
    actions = ['refresh_fmp_data', 'verify_custom_status']

    def save_model(self, request, obj, form, change):
        from external_data.fmp.dispatch import fetch_asset_data

        if not change:  # creating new stock
            obj.ticker = obj.ticker.upper()
            obj.is_custom = form.cleaned_data.get('is_custom', False)

            # Try to fetch data from FMP (even if custom)
            success = fetch_asset_data(obj, 'stock', verify_custom=True)

            if not success and not obj.is_custom:
                self.message_user(
                    request,
                    f"Could not fetch FMP data for {obj.ticker}.",
                    level=messages.WARNING
                )
            elif not success and obj.is_custom:
                self.message_user(
                    request,
                    f"Creating {obj.ticker} as custom stock.",
                    level=messages.INFO
                )

            try:
                obj.full_clean()
                obj.save()
                self.message_user(
                    request,
                    f"Stock {obj.ticker} created successfully.",
                    level=messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to create stock {obj.ticker}: {str(e)}",
                    level=messages.ERROR
                )
                raise
        else:  # updating existing
            if not obj.is_custom:
                success = fetch_asset_data(obj, 'stock', verify_custom=True)
                if not success:
                    self.message_user(
                        request,
                        f"Could not update FMP data for {obj.ticker}.",
                        level=messages.WARNING
                    )
            obj.save()
            self.message_user(
                request,
                f"Stock {obj.ticker} updated successfully.",
                level=messages.SUCCESS
            )

    def refresh_fmp_data(self, request, queryset):
        from external_data.fmp.dispatch import fetch_asset_data

        updated = 0
        failed = 0

        for stock in queryset:
            success = fetch_asset_data(stock, 'stock', verify_custom=True)
            if success:
                if stock.is_custom:
                    stock.is_custom = False
                    logger.info(f"Converted {stock.ticker} from custom to FMP")
                stock.save()
                updated += 1
            else:
                failed += 1

        if updated:
            self.message_user(
                request,
                f"Successfully refreshed {updated} stock(s).",
                level=messages.SUCCESS
            )
        if failed:
            self.message_user(
                request,
                f"Failed to refresh {failed} stock(s).",
                level=messages.WARNING
            )

    refresh_fmp_data.short_description = "Refresh FMP data for selected stocks"

    def verify_custom_status(self, request, queryset):
        from external_data.fmp.dispatch import fetch_asset_data 
        verified_custom = 0
        converted_to_fmp = 0
        failed = 0
        for stock in queryset:
            was_custom = stock.is_custom
            success = fetch_asset_data(stock, 'stock', verify_custom=True)
            if success:
                if was_custom:
                    stock.is_custom = False
                    converted_to_fmp += 1
                    logger.info(f"Converted {stock.ticker} from custom to FMP")
                stock.save()
            else:
                if not stock.is_custom:
                    stock.is_custom = True
                    stock.price = None
                    stock.name = None
                    stock.sector = None
                    stock.industry = None
                    stock.currency = None
                    stock.dividend_yield = None
                    stock.pe_ratio = None
                    stock.quote_type = None
                    stock.average_volume = None
                    stock.volume = None
                    stock.last_updated = None
                    stock.save()
                    verified_custom += 1
                    logger.info(f"Verified {stock.ticker} as custom")
                else:
                    verified_custom += 1
            if not success and not stock.is_custom:
                failed += 1

        messages_list = []
        if converted_to_fmp:
            messages_list.append(
                f"Converted {converted_to_fmp} stocks from custom to FMP.")
        if verified_custom:
            messages_list.append(
                f"Verified {verified_custom} stocks as custom.")
        if failed:
            messages_list.append(f"Failed to process {failed} stocks.")
        if messages_list:
            self.message_user(
                request,
                " ".join(messages_list),
                level=messages.SUCCESS if not failed else messages.WARNING
            )

    verify_custom_status.short_description = "Verify custom status of selected stocks"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.is_custom:
            for field in ['currency', 'dividend_yield', 'pe_ratio', 'quote_type', 'average_volume', 'volume']:
                form.base_fields[field].required = False
        return form


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = [
        'holding_link', 'stock_link', 'self_managed_account_link', 'quantity', 'purchase_price',
        'purchase_date', 'current_value', 'performance', 'investment_theme'
    ]
    list_display_links = ['holding_link']
    list_filter = [
        'self_managed_account__stock_portfolio__portfolio__profile',
        'stock__quote_type', 'stock__sector', 'stock__is_adr', 'investment_theme'
    ]
    search_fields = ['stock__ticker',
                     'stock__name', 'self_managed_account__name']
    list_editable = ['quantity', 'purchase_price', 'purchase_date']
    list_per_page = 50
    fields = [
        'self_managed_account', 'stock', 'quantity', 'purchase_price',
        'purchase_date', 'investment_theme'
    ]
    autocomplete_fields = ['stock', 'self_managed_account']
    actions = ['refresh_holding_values']

    def holding_link(self, obj):
        url = reverse(
            'admin:stock_portfolio_stockholding_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, f"{obj.stock.ticker} ({obj.self_managed_account.name})")
    holding_link.short_description = 'Holding'

    def stock_link(self, obj):
        url = reverse('admin:stocks_stock_change', args=[obj.stock.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock.ticker)
    stock_link.short_description = 'Stock'

    def self_managed_account_link(self, obj):
        url = reverse('admin:stock_portfolio_selfmanagedaccount_change', args=[
                      obj.self_managed_account.id])
        return format_html('<a href="{}">{}</a>', url, obj.self_managed_account.name)
    self_managed_account_link.short_description = 'Account'

    def current_value(self, obj):
        return obj.get_current_value()
    current_value.short_description = 'Current Value'

    def performance(self, obj):
        perf = obj.get_performance()
        return f"{perf:.2f}%" if perf is not None else "-"

    def refresh_holding_values(self, request, queryset):
        updated = 0
        for holding in queryset:
            try:
                if holding.stock.fetch_fmp_data(force_update=True):
                    holding.stock.save()
                    updated += 1
            except Exception as e:
                logger.error(
                    f"Failed to refresh {holding.stock.ticker}: {str(e)}")
        self.message_user(
            request,
            f"Refreshed {updated} holdings' stock values.",
            level='success' if updated else 'warning'
        )
    refresh_holding_values.short_description = "Refresh stock values from FMP"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('stock', 'self_managed_account', 'investment_theme')